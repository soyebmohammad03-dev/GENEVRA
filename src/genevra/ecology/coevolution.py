"""Phase 15.8: a controlled co-evolution framework.

Two "species" are two founding sub-populations sharing one
`ContinuousEvolutionEngine` run (one `SharedGridWorld`, one resource
pool): the first half of the initial population is species A, the second
half species B, and every descendant inherits its ultimate founder's
species via `LineageTracker.ancestors()`. This is a real, honest
co-evolution setup — two lineages under shared ecological pressure,
tracked separately — not a claim of two biologically distinct species;
`docs/co_evolution.md` documents that "species" here means "founding
sub-population," nothing more.

Per-species trajectories are reconstructed entirely from
`LineageEvent.generation`/`death_generation` (no extra per-step engine
hook is needed): at each sampled step, a species' population size is the
count of its members born by then and not yet dead.
"""

from __future__ import annotations

import dataclasses
from dataclasses import dataclass
from typing import Any

from genevra.evolution.continuous import ContinuousEvolutionConfig, ContinuousEvolutionEngine
from genevra.evolution.lineage import LineageEvent, LineageTracker


@dataclass(frozen=True)
class SpeciesTrajectoryPoint:
    step: int
    population_size: int
    mean_learning_strategy: tuple[float, float, float] | None


@dataclass(frozen=True)
class CoEvolutionTrajectory:
    species_a: tuple[SpeciesTrajectoryPoint, ...]
    species_b: tuple[SpeciesTrajectoryPoint, ...]

    def to_dict(self) -> dict[str, Any]:
        return dataclasses.asdict(self)


def _founder_species(events: dict[int, LineageEvent], individual_id: int, split_id: int) -> str:
    current = individual_id
    seen: set[int] = set()
    while events[current].parent_ids and current not in seen:
        seen.add(current)
        current = events[current].parent_ids[0]
    return "a" if current < split_id else "b"


def build_coevolution_trajectory(
    lineage: LineageTracker, initial_population: int, sample_steps: list[int]
) -> CoEvolutionTrajectory:
    events = {e.individual_id: e for e in lineage.events()}
    split_id = initial_population // 2
    species_of = {iid: _founder_species(events, iid, split_id) for iid in events}

    def snapshot(step: int, species: str) -> SpeciesTrajectoryPoint:
        alive = [
            e
            for iid, e in events.items()
            if species_of[iid] == species
            and e.generation <= step
            and (e.death_generation is None or e.death_generation > step)
        ]
        if not alive:
            return SpeciesTrajectoryPoint(step, 0, None)
        strategies = [e.learning_strategy for e in alive]
        rate, gate, decay = (sum(vals) / len(vals) for vals in zip(*strategies, strict=True))
        return SpeciesTrajectoryPoint(step, len(alive), (rate, gate, decay))

    return CoEvolutionTrajectory(
        species_a=tuple(snapshot(s, "a") for s in sample_steps),
        species_b=tuple(snapshot(s, "b") for s in sample_steps),
    )


@dataclass(frozen=True)
class CoEvolutionComparison:
    final_population_a: int
    final_population_b: int
    species_a_extinct: bool
    species_b_extinct: bool
    final_strategy_divergence: float | None
    """Euclidean distance between the two species' final
    `mean_learning_strategy` vectors. `None` if either species is extinct
    (no strategy to compare) at the final sampled step."""

    def to_dict(self) -> dict[str, Any]:
        return dataclasses.asdict(self)


class CoEvolutionAnalyzer:
    def compare(self, trajectory: CoEvolutionTrajectory) -> CoEvolutionComparison:
        final_a = trajectory.species_a[-1] if trajectory.species_a else None
        final_b = trajectory.species_b[-1] if trajectory.species_b else None
        pop_a = final_a.population_size if final_a else 0
        pop_b = final_b.population_size if final_b else 0
        divergence: float | None = None
        if (
            final_a
            and final_b
            and final_a.mean_learning_strategy
            and final_b.mean_learning_strategy
        ):
            divergence = (
                sum(
                    (x - y) ** 2
                    for x, y in zip(
                        final_a.mean_learning_strategy, final_b.mean_learning_strategy, strict=True
                    )
                )
                ** 0.5
            )
        return CoEvolutionComparison(
            final_population_a=pop_a,
            final_population_b=pop_b,
            species_a_extinct=pop_a == 0,
            species_b_extinct=pop_b == 0,
            final_strategy_divergence=divergence,
        )


def run_coevolution_experiment(
    config: ContinuousEvolutionConfig, log_every_override: int | None = None
) -> tuple[ContinuousEvolutionEngine, CoEvolutionTrajectory]:
    """Runs one `ContinuousEvolutionEngine` and reconstructs the
    two-founding-group trajectory from its lineage. `log_every_override`
    controls trajectory sampling density independent of the engine's own
    snapshot cadence (lineage-based reconstruction doesn't need them to
    match)."""
    engine = ContinuousEvolutionEngine(config)
    engine.run()
    step = log_every_override or config.log_every
    sample_steps = list(range(0, config.total_steps + 1, step))
    trajectory = build_coevolution_trajectory(
        engine.lineage, config.initial_population, sample_steps
    )
    return engine, trajectory


__all__ = [
    "SpeciesTrajectoryPoint",
    "CoEvolutionTrajectory",
    "build_coevolution_trajectory",
    "CoEvolutionComparison",
    "CoEvolutionAnalyzer",
    "run_coevolution_experiment",
]
