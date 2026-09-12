"""Phase 13.8: deepened `LearningStrategy` analysis — lineage
inheritance and environment dependence — built directly on
`LineageTracker` records and `genevra.analysis.strategy_clustering`
(persistence/turnover already exist there and are not reimplemented
here).
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

import numpy as np

from genevra.analysis.learning_strategy import LearningStrategy, WeightedStrategyDistance
from genevra.evolution.lineage import LineageEvent


@dataclass(frozen=True)
class LineageInheritanceResult:
    n_parent_child_pairs: int
    mean_strategy_distance: float
    std_strategy_distance: float
    note: str = (
        "Parent-to-child LearningStrategy distance at birth, across every "
        "parent/child pair this lineage tracker recorded. A small mean distance is "
        "consistent with strong heritability of the sampled strategy dimensions "
        "under GENEVRA's mutation model; it is not a heritability estimate in the "
        "quantitative-genetics sense (no variance decomposition is performed)."
    )


def lineage_strategy_inheritance(
    events: Sequence[LineageEvent], distance: WeightedStrategyDistance | None = None
) -> LineageInheritanceResult:
    metric = distance if distance is not None else WeightedStrategyDistance()
    by_id = {e.individual_id: e for e in events}
    distances: list[float] = []
    for event in events:
        if not event.parent_ids:
            continue
        parent = by_id.get(event.parent_ids[0])
        if parent is None:
            continue
        child_strategy = LearningStrategy(*event.learning_strategy)
        parent_strategy = LearningStrategy(*parent.learning_strategy)
        distances.append(metric.strategy_distance(child_strategy, parent_strategy))
    if not distances:
        return LineageInheritanceResult(
            n_parent_child_pairs=0, mean_strategy_distance=0.0, std_strategy_distance=0.0
        )
    arr = np.asarray(distances)
    return LineageInheritanceResult(
        n_parent_child_pairs=len(distances),
        mean_strategy_distance=float(np.mean(arr)),
        std_strategy_distance=float(np.std(arr)),
    )


@dataclass(frozen=True)
class EnvironmentDependenceResult:
    condition_means: dict[str, tuple[float, float, float]]
    """condition_id -> mean (learning_rate, plasticity_gate, decay)."""
    note: str = (
        "Per-condition mean evolved LearningStrategy, one row per condition_id. "
        "Comparing rows is a descriptive comparison across the conditions actually "
        "run; no significance test is applied here — use "
        "genevra.analysis.comparison.ComparisonRunner for that."
    )


def strategy_environment_dependence(
    strategies_by_condition: dict[str, Sequence[LearningStrategy]],
) -> EnvironmentDependenceResult:
    """`strategies_by_condition` maps a condition_id (e.g. from
    `genevra.experiments.conditions`) to the final-generation
    `LearningStrategy` population evolved under it. Answers "does one
    strategy dominate under certain environmental regimes?" descriptively
    — the caller decides whether an observed difference is
    scientifically or only numerically meaningful."""
    means: dict[str, tuple[float, float, float]] = {}
    for condition_id, strategies in strategies_by_condition.items():
        if not strategies:
            continue
        vectors = np.array([s.as_vector() for s in strategies])
        mean = vectors.mean(axis=0)
        means[condition_id] = (float(mean[0]), float(mean[1]), float(mean[2]))
    return EnvironmentDependenceResult(condition_means=means)


__all__ = [
    "LineageInheritanceResult",
    "lineage_strategy_inheritance",
    "EnvironmentDependenceResult",
    "strategy_environment_dependence",
]
