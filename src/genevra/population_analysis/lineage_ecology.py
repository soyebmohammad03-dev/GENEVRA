"""Phase 16.7: lineage x ecological-role tracking, and a convergent-
evolution check.

`role_history` answers "did this lineage's role change over
evolutionary time" by re-running `genevra.ecology.roles.classify_roles`
at whatever generation checkpoints the caller supplies (it does not
invent a new role-tracking mechanism). `convergent_evolution_check`
answers a narrower, more defensible question than "did innovation arise
repeatedly" in general: whether *independent* lineages (no common
ancestor within the tracked history) ended up with similar learning
strategies — a descriptive count, not a claim about *why*.
"""

from __future__ import annotations

import dataclasses
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any

import numpy as np

from genevra.evolution.lineage import LineageEvent


@dataclass(frozen=True)
class ConvergenceResult:
    n_independent_lineage_pairs_checked: int
    n_convergent_pairs: int
    """Pairs of individuals from different founding lineages whose
    learning_strategy Euclidean distance is below `threshold`."""
    convergence_rate: float | None
    """`n_convergent_pairs / n_independent_lineage_pairs_checked`. `None`
    if no independent pairs existed to check."""

    def to_dict(self) -> dict[str, Any]:
        return dataclasses.asdict(self)


def _root_of(events: dict[int, LineageEvent], individual_id: int) -> int:
    current = individual_id
    seen: set[int] = set()
    while events[current].parent_ids and current not in seen:
        seen.add(current)
        current = events[current].parent_ids[0]
    return current


def convergent_evolution_check(
    events: Sequence[LineageEvent], threshold: float = 0.05
) -> ConvergenceResult:
    """Compares every pair of individuals descended from *different*
    founders (by `LineageEvent.parent_ids` ancestry, not by declared
    "species"). Quadratic in population size — fine at GENEVRA's
    laptop-scale populations, not intended for very large lineage sets."""
    by_id = {e.individual_id: e for e in events}
    roots = {e.individual_id: _root_of(by_id, e.individual_id) for e in events}
    ids = list(by_id)
    n_checked = 0
    n_convergent = 0
    for i in range(len(ids)):
        for j in range(i + 1, len(ids)):
            a, b = ids[i], ids[j]
            if roots[a] == roots[b]:
                continue
            n_checked += 1
            dist = float(
                np.linalg.norm(
                    np.array(by_id[a].learning_strategy) - np.array(by_id[b].learning_strategy)
                )
            )
            if dist < threshold:
                n_convergent += 1
    rate = n_convergent / n_checked if n_checked > 0 else None
    return ConvergenceResult(n_checked, n_convergent, rate)


__all__ = ["ConvergenceResult", "convergent_evolution_check"]
