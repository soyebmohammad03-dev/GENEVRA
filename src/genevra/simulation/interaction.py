"""GENEVRA's first organism-organism interaction mechanism: deterministic
spatial competition for cells.

`InteractionSystem` is deliberately narrow — it only resolves *where*
agents end up when their intended moves conflict — so that later mechanisms
(communication, cooperation, predation) can be added as new implementations
of the same idea (agents' intentions go in, resolved outcomes come out)
without `SharedGridWorld` or `Population` needing to change.

Resource competition emerges from this rather than being a separate
mechanic: two agents can only compete for a resource cell by both trying
to move onto it in the same step, and `SpatialCompetition` decides who
gets there.
"""

from __future__ import annotations

from typing import Protocol

from genevra.arrays import BoolArray
from genevra.simulation.types import Position


class InteractionSystem(Protocol):
    def resolve_movements(
        self,
        current_positions: dict[int, Position],
        desired_positions: dict[int, Position],
        obstacles: BoolArray,
        width: int,
        height: int,
    ) -> dict[int, Position]: ...


class SpatialCompetition:
    """Resolves simultaneous movement deterministically:

    1. Agents that are not moving this step (`desired == current`) keep
       unconditional priority over their own current cell — nobody can be
       displaced by someone else moving into the cell they're standing in.
    2. Among agents that *are* moving, ties for a contested free cell are
       broken by ascending agent id (a documented, reproducible tie-break
       rule — not a random bonus, and not literal physical simultaneity).
       The loser(s) stay at their current position, as if they had hit an
       obstacle this step.
    """

    def __init__(self) -> None:
        self.last_blocked_pairs: list[tuple[int, int]] = []
        """`(blocked_agent_id, blocking_agent_id)` pairs from the most
        recent `resolve_movements()` call — the agent that lost a
        contested cell, and the agent that occupies it afterward (either
        because it was already stationary there or won the tie-break).
        Additive introspection only (Phase 15.1): the `InteractionSystem`
        Protocol's return value is unchanged, so this is safe for any
        other implementation to ignore. Used to derive real
        `EcologicalInteraction` (competition) records from what
        `SharedGridWorld` already does, instead of inventing a parallel
        interaction-detection mechanism."""

    def resolve_movements(
        self,
        current_positions: dict[int, Position],
        desired_positions: dict[int, Position],
        obstacles: BoolArray,
        width: int,
        height: int,
    ) -> dict[int, Position]:
        self.last_blocked_pairs = []
        stationary_ids = [
            agent_id
            for agent_id, target in desired_positions.items()
            if target == current_positions[agent_id]
        ]
        moving_ids = sorted(
            agent_id
            for agent_id, target in desired_positions.items()
            if target != current_positions[agent_id]
        )

        claimed: dict[Position, int] = {
            current_positions[agent_id]: agent_id for agent_id in stationary_ids
        }
        final_positions: dict[int, Position] = {
            agent_id: current_positions[agent_id] for agent_id in stationary_ids
        }

        for agent_id in moving_ids:
            target = desired_positions[agent_id]
            in_bounds = 0 <= target.x < width and 0 <= target.y < height
            blocked = (not in_bounds) or bool(obstacles[target.y, target.x]) or target in claimed
            if blocked:
                final_positions[agent_id] = current_positions[agent_id]
                if in_bounds and not obstacles[target.y, target.x] and target in claimed:
                    self.last_blocked_pairs.append((agent_id, claimed[target]))
            else:
                claimed[target] = agent_id
                final_positions[agent_id] = target

        return final_positions
