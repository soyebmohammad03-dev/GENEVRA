"""Phase 15.5/15.6: spatial structure as multiple `ContinuousEvolutionEngine`
patches with configurable migration between them.

GENEVRA's `SharedGridWorld` is one connected grid; it does not itself
model disconnected patches. Rather than inventing a second grid engine,
"patchy"/"fragmented"/"connected" spatial regimes here are each an
independent `ContinuousEvolutionEngine` (its own `SharedGridWorld`,
population, and lineage), with a configurable connectivity graph
controlling which patches migrants can move between. "Well-mixed" is the
degenerate one-patch case (no migration possible or needed).

No organism ever senses which patch it is in, or another patch's state —
each patch's `SharedGridWorld` observation boundary is unchanged; the
metapopulation-level connectivity/migration bookkeeping is entirely
simulator-internal, exactly like grid coordinates.
"""

from __future__ import annotations

import dataclasses
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

import numpy as np

from genevra.evolution.continuous import (
    ContinuousEvolutionConfig,
    ContinuousEvolutionEngine,
    EcologicalSnapshot,
)
from genevra.evolution.lineage import LineageEvent
from genevra.metrics.diversity import EuclideanDistance, mean_pairwise_distance


class SpatialRegime(StrEnum):
    WELL_MIXED = "well_mixed"
    """A single patch (degenerate case: no migration graph to speak of)."""
    PATCHY = "patchy"
    """N patches, ring connectivity (each patch connects to two
    neighbors) — migrants take multiple hops to reach a distant patch."""
    FRAGMENTED = "fragmented"
    """N patches, no connectivity at all (isolated populations; the
    `migration_probability` parameter has no effect)."""
    CONNECTED = "connected"
    """N patches, fully connected (every patch reachable from every
    other patch in one hop)."""


def build_connectivity(regime: SpatialRegime, n_patches: int) -> dict[int, tuple[int, ...]]:
    if n_patches < 1:
        raise ValueError("n_patches must be positive")
    if regime is SpatialRegime.WELL_MIXED:
        if n_patches != 1:
            raise ValueError("WELL_MIXED requires exactly 1 patch")
        return {0: ()}
    if regime is SpatialRegime.FRAGMENTED:
        return {i: () for i in range(n_patches)}
    if regime is SpatialRegime.PATCHY:
        if n_patches < 2:
            return {0: ()}
        return {i: ((i - 1) % n_patches, (i + 1) % n_patches) for i in range(n_patches)}
    if regime is SpatialRegime.CONNECTED:
        return {i: tuple(j for j in range(n_patches) if j != i) for i in range(n_patches)}
    raise ValueError(f"unknown regime {regime!r}")


@dataclass(frozen=True)
class MigrationConfig:
    migration_probability: float = 0.0
    """Per eligible individual, per migration event, probability of
    migrating to a randomly-chosen connected neighbor patch."""
    migration_interval: int = 10
    """Steps between migration opportunities."""
    connectivity: dict[int, tuple[int, ...]] = field(default_factory=dict)
    """patch_id -> neighbor patch ids it can migrate to."""

    def __post_init__(self) -> None:
        if not 0.0 <= self.migration_probability <= 1.0:
            raise ValueError("migration_probability must be in [0, 1]")
        if self.migration_interval <= 0:
            raise ValueError("migration_interval must be positive")


@dataclass(frozen=True)
class MetapopulationSnapshot:
    step: int
    per_patch: dict[int, EcologicalSnapshot]
    migrations_since_last_snapshot: int


@dataclass(frozen=True)
class PatchDiversitySummary:
    patch_id: int
    genotypic_diversity: float
    population_size: int
    lineage_persistence: float | None
    """Fraction of this patch's generation-0 founders (individuals
    present at metapopulation step 0) with a living descendant still in
    *this* patch at the end of the run. `None` if the patch had no
    generation-0 founders (e.g. it started empty and only received
    migrants)."""

    def to_dict(self) -> dict[str, Any]:
        return dataclasses.asdict(self)


class Metapopulation:
    """Runs N `ContinuousEvolutionEngine` patches in lockstep, migrating
    individuals between connected patches on a fixed interval."""

    def __init__(
        self,
        patch_configs: list[ContinuousEvolutionConfig],
        migration: MigrationConfig,
        seed: int,
    ) -> None:
        if not patch_configs:
            raise ValueError("at least one patch config is required")
        self._migration = migration
        self._rng = np.random.default_rng(seed)
        self.patches: dict[int, ContinuousEvolutionEngine] = {
            i: ContinuousEvolutionEngine(cfg) for i, cfg in enumerate(patch_configs)
        }
        self.history: list[MetapopulationSnapshot] = []
        self._founders_by_patch: dict[int, set[int]] = {}

    def initialize(self) -> None:
        for patch_id, engine in self.patches.items():
            engine.initialize()
            self._founders_by_patch[patch_id] = set(engine.population)

    def run(self, total_steps: int) -> list[MetapopulationSnapshot]:
        self.initialize()
        for step in range(total_steps):
            for engine in self.patches.values():
                engine.step()
            migrations = 0
            if step > 0 and step % self._migration.migration_interval == 0:
                migrations = self._maybe_migrate()
            log_every = next(iter(self.patches.values())).config.log_every
            if step % log_every == 0:
                self.history.append(
                    MetapopulationSnapshot(
                        step=step,
                        per_patch={
                            pid: engine.history[-1]
                            for pid, engine in self.patches.items()
                            if engine.history
                        },
                        migrations_since_last_snapshot=migrations,
                    )
                )
        return self.history

    def _maybe_migrate(self) -> int:
        migrations = 0
        for patch_id, engine in self.patches.items():
            neighbors = self._migration.connectivity.get(patch_id, ())
            if not neighbors:
                continue
            eligible = list(engine.population)
            for agent_id in eligible:
                if self._rng.random() >= self._migration.migration_probability:
                    continue
                if len(engine.population) <= 1:
                    continue  # never fully empty a patch via migration
                target_patch_id = int(self._rng.choice(neighbors))
                target = self.patches[target_patch_id]
                if len(target.population) >= target.config.max_population:
                    continue
                genome = engine.emigrate(agent_id)
                target.spawn_migrant(genome)
                migrations += 1
        return migrations

    def diversity_by_patch(self) -> list[PatchDiversitySummary]:
        summaries = []
        for patch_id, engine in self.patches.items():
            vectors = [living.genome.controller_weights for living in engine.population.values()]
            diversity = mean_pairwise_distance(vectors, EuclideanDistance())
            founders = self._founders_by_patch.get(patch_id, set())
            persistence: float | None = None
            if founders:
                events = {e.individual_id: e for e in engine.lineage.events()}
                children_of: dict[int, list[int]] = {}
                for e in events.values():
                    for p in e.parent_ids:
                        children_of.setdefault(p, []).append(e.individual_id)

                def survives(
                    founder_id: int,
                    events: dict[int, LineageEvent] = events,
                    children_of: dict[int, list[int]] = children_of,
                ) -> bool:
                    stack = [founder_id]
                    seen: set[int] = set()
                    while stack:
                        current = stack.pop()
                        if current in seen:
                            continue
                        seen.add(current)
                        event = events.get(current)
                        if event is not None and event.death_generation is None:
                            return True
                        stack.extend(children_of.get(current, []))
                    return False

                persistence = sum(1 for f in founders if survives(f)) / len(founders)
            summaries.append(
                PatchDiversitySummary(
                    patch_id=patch_id,
                    genotypic_diversity=diversity,
                    population_size=len(engine.population),
                    lineage_persistence=persistence,
                )
            )
        return summaries


__all__ = [
    "SpatialRegime",
    "build_connectivity",
    "MigrationConfig",
    "MetapopulationSnapshot",
    "PatchDiversitySummary",
    "Metapopulation",
]
