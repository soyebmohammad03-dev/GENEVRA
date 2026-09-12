"""Phase 15.1: a typed record of one organism-organism interaction.

GENEVRA's only implemented organism-organism mechanism is spatial
competition for grid cells (`genevra.simulation.interaction.
SpatialCompetition`) and, indirectly, competition for the resources those
cells hold. `EcologicalInteraction` records are *derived* from what that
mechanism already does (via `SpatialCompetition.last_blocked_pairs`),
never fabricated or inferred from correlation.

Cooperation/costly-helping (Phase 15.4) is NOT implemented: GENEVRA's
`Action` space (`genevra.simulation.types.Action`) has no action that
transfers resources or fitness to another agent, and every controller's
output size is pinned to `len(Action)` throughout the organism/evolution
stack. Adding one would change the action space for every existing
genome, architecture, and stored result — a backward-incompatible change
this phase does not make. This is documented here, not silently skipped:
see `docs/interactions.md` for what a `SHARE` action would require.
"""

from __future__ import annotations

import dataclasses
import math
from collections import Counter
from collections.abc import Sequence
from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from genevra.simulation.interaction import SpatialCompetition
from genevra.simulation.shared_grid_world import SharedGridWorld


class InteractionType(StrEnum):
    """Interaction kinds GENEVRA can actually derive from simulation
    state. `COOPERATION` is deliberately absent — see module docstring."""

    COMPETITION = "competition"
    """Two agents both tried to move onto the same free cell this step;
    one was blocked. Derived exactly from `SpatialCompetition.
    last_blocked_pairs`, not inferred."""
    RESOURCE_ACQUISITION = "resource_acquisition"
    """One agent consumed a resource cell another agent could have
    reached — recorded as a self-interaction with the environment
    (`target is None`) since GENEVRA does not track "who else was
    nearby and wanted it," only that acquisition happened."""


class InteractionOutcome(StrEnum):
    WIN = "win"
    LOSE = "lose"
    NEUTRAL = "neutral"


@dataclass(frozen=True)
class EcologicalContext:
    """Provenance for one interaction record: which experiment/seed/step
    it came from, so records from different runs are never silently
    pooled as if they were one continuous interaction history."""

    experiment_id: str
    seed: int
    generation_or_step: int


@dataclass(frozen=True)
class EcologicalInteraction:
    actor: int
    target: int | None
    """`None` for a `RESOURCE_ACQUISITION` record (interaction with the
    environment, not another agent)."""
    interaction_type: InteractionType
    outcome: InteractionOutcome
    strength: float = 1.0
    """Currently always 1.0 (one discrete event); a placeholder for a
    future continuous-strength interaction, not a fabricated gradient."""
    resource_transfer: float = 0.0
    fitness_consequence: float | None = None
    behavioral_consequence: str | None = None
    environmental_consequence: str | None = None
    context: EcologicalContext | None = None

    def to_dict(self) -> dict[str, Any]:
        d = dataclasses.asdict(self)
        d["interaction_type"] = self.interaction_type.value
        d["outcome"] = self.outcome.value
        return d


def derive_competition_interactions(
    interaction_system: SpatialCompetition,
    context: EcologicalContext,
) -> list[EcologicalInteraction]:
    """One `EcologicalInteraction` per blocked-move event recorded during
    the most recent `SharedGridWorld.step()` call, read from
    `interaction_system.last_blocked_pairs`."""
    return [
        EcologicalInteraction(
            actor=blocked_id,
            target=winner_id,
            interaction_type=InteractionType.COMPETITION,
            outcome=InteractionOutcome.LOSE,
            context=context,
        )
        for blocked_id, winner_id in interaction_system.last_blocked_pairs
    ]


def derive_resource_acquisition_interactions(
    rewards: dict[int, float],
    resource_types: dict[int, str | None],
    context: EcologicalContext,
) -> list[EcologicalInteraction]:
    """One record per agent that actually ate something this step
    (`rewards[agent_id] > 0`), tagged with which resource type."""
    return [
        EcologicalInteraction(
            actor=agent_id,
            target=None,
            interaction_type=InteractionType.RESOURCE_ACQUISITION,
            outcome=InteractionOutcome.WIN,
            resource_transfer=amount,
            environmental_consequence=resource_types.get(agent_id),
            context=context,
        )
        for agent_id, amount in rewards.items()
        if amount > 0
    ]


def require_shared_grid_world_with_spatial_competition(
    world: SharedGridWorld,
) -> SpatialCompetition:
    """`derive_competition_interactions` needs the concrete
    `SpatialCompetition` implementation (for `last_blocked_pairs`), not
    just the `InteractionSystem` protocol. Raises with a clear message if
    a `world` was built with a different `InteractionSystem`, rather than
    silently returning no interactions."""
    system = world.interaction_system
    if not isinstance(system, SpatialCompetition):
        raise TypeError(
            "ecological interaction derivation currently requires SharedGridWorld's "
            f"default SpatialCompetition interaction system, got {type(system).__name__}"
        )
    return system


@dataclass(frozen=True)
class InsufficientNetworkData:
    reason: str


@dataclass(frozen=True)
class InteractionNetwork:
    """A lightweight interaction graph built from a list of
    `EcologicalInteraction` records — no graph-library dependency
    (see `docs/interactions.md` for what that would add)."""

    interactions: tuple[EcologicalInteraction, ...]

    @property
    def nodes(self) -> set[int]:
        nodes: set[int] = set()
        for interaction in self.interactions:
            nodes.add(interaction.actor)
            if interaction.target is not None:
                nodes.add(interaction.target)
        return nodes

    def degree(self) -> dict[int, int]:
        """Number of agent-agent interaction records each node
        participates in, as either actor or target."""
        counts: Counter[int] = Counter()
        for interaction in self.interactions:
            if interaction.target is None:
                continue
            counts[interaction.actor] += 1
            counts[interaction.target] += 1
        return dict(counts)

    def density(self) -> float | InsufficientNetworkData:
        """edges / (n * (n-1)) over distinct agent-agent edges (undirected,
        deduplicated actor/target pairs). Requires >= 2 nodes."""
        edges = {frozenset((i.actor, i.target)) for i in self.interactions if i.target is not None}
        n = len(self.nodes)
        if n < 2:
            return InsufficientNetworkData(f"only {n} node(s); density requires >= 2")
        return len(edges) / (n * (n - 1) / 2)

    def interaction_type_diversity(self) -> float:
        """Shannon entropy (natural log) over the distribution of
        `interaction_type` values, 0.0 when there is only one type or no
        interactions."""
        counts = Counter(i.interaction_type for i in self.interactions)
        total = sum(counts.values())
        if total == 0 or len(counts) < 2:
            return 0.0
        return -sum((c / total) * math.log(c / total) for c in counts.values() if c > 0)


def build_interaction_network(interactions: Sequence[EcologicalInteraction]) -> InteractionNetwork:
    return InteractionNetwork(interactions=tuple(interactions))


__all__ = [
    "InteractionType",
    "InteractionOutcome",
    "EcologicalContext",
    "EcologicalInteraction",
    "InteractionNetwork",
    "InsufficientNetworkData",
    "derive_competition_interactions",
    "derive_resource_acquisition_interactions",
    "require_shared_grid_world_with_spatial_competition",
    "build_interaction_network",
]
