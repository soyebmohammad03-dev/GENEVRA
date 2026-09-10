"""Change-point analysis (Phase 9.7), candidate evolutionary-regime/event
detection built on it (Phase 9.6), and a structured record for the
resulting candidate transitions (Phase 9.8).

**None of this proves a causal event.** `detect_change_points` and
`detect_regime_transitions` identify statistically interesting
discontinuities in a trajectory — candidates for a researcher to
investigate further (e.g. via `genevra.analysis.counterfactual` or a
follow-up experiment), never a verdict that "an event happened here" in
any deeper sense.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any

import numpy as np

_LIMITATION_NOTE = (
    "A change point marks a statistically unusual shift in one metric's trajectory "
    "under this detector's method and configuration. It is a candidate for "
    "investigation, not proof that a discrete biological/evolutionary event "
    "occurred at that generation."
)


@dataclass(frozen=True)
class ChangePointConfig:
    """Every threshold explicit (Phase 9.7's "avoid hard-coded arbitrary
    thresholds" — meaning: no thresholds buried in function bodies, all
    exposed here for sensitivity analysis)."""

    min_segment_length: int = 3
    significance_level: float = 0.05
    num_permutations: int = 500
    max_change_points: int = 5

    def __post_init__(self) -> None:
        if self.min_segment_length < 1:
            raise ValueError("min_segment_length must be >= 1")
        if not 0.0 < self.significance_level < 1.0:
            raise ValueError("significance_level must be in (0, 1)")
        if self.num_permutations < 1:
            raise ValueError("num_permutations must be >= 1")
        if self.max_change_points < 0:
            raise ValueError("max_change_points must be >= 0")


@dataclass(frozen=True)
class ChangePoint:
    metric_name: str
    index: int
    generation: int
    magnitude: float
    before_mean: float
    after_mean: float
    p_value: float
    method: str = "cusum_permutation"
    limitation_note: str = field(default=_LIMITATION_NOTE)


def detect_change_points(
    values: Sequence[float],
    metric_name: str,
    rng: np.random.Generator,
    generations: Sequence[int] | None = None,
    config: ChangePointConfig | None = None,
) -> list[ChangePoint]:
    """Recursive binary segmentation: find the single split that maximizes
    a scale-normalized mean-shift statistic (a CUSUM-style statistic),
    test its significance via permutation (shuffle the series, recompute
    the best-split statistic, compare to the observed value — the
    standard non-parametric test for "is there at least one change point"
    also used by `genevra.analysis.aggregation.permutation_test`
    elsewhere in this codebase), then recurse into the two resulting
    segments if the split was significant and both sides are long enough.
    Stops at `config.max_change_points`."""
    cfg = config if config is not None else ChangePointConfig()
    gens = list(generations) if generations is not None else list(range(len(values)))
    if len(gens) != len(values):
        raise ValueError("generations must be the same length as values")

    found: list[ChangePoint] = []
    _segment(list(values), gens, metric_name, rng, cfg, found, offset=0)
    found.sort(key=lambda cp: cp.index)
    return found[: cfg.max_change_points]


def _segment(
    values: list[float],
    generations: list[int],
    metric_name: str,
    rng: np.random.Generator,
    cfg: ChangePointConfig,
    found: list[ChangePoint],
    offset: int,
) -> None:
    if len(found) >= cfg.max_change_points:
        return
    n = len(values)
    if n < 2 * cfg.min_segment_length:
        return

    split, statistic = _best_split(values, cfg.min_segment_length)
    if split is None or statistic is None:
        return

    permuted_max = np.empty(cfg.num_permutations, dtype=np.float64)
    pool = np.asarray(values, dtype=np.float64).copy()
    for i in range(cfg.num_permutations):
        rng.shuffle(pool)
        _, permuted_stat = _best_split(list(pool), cfg.min_segment_length)
        permuted_max[i] = permuted_stat if permuted_stat is not None else 0.0
    p_value = float((np.sum(permuted_max >= statistic) + 1) / (cfg.num_permutations + 1))

    if p_value > cfg.significance_level:
        return

    before = values[:split]
    after = values[split:]
    found.append(
        ChangePoint(
            metric_name=metric_name,
            index=offset + split,
            generation=generations[split],
            magnitude=float(np.mean(after) - np.mean(before)),
            before_mean=float(np.mean(before)),
            after_mean=float(np.mean(after)),
            p_value=p_value,
        )
    )
    _segment(before, generations[:split], metric_name, rng, cfg, found, offset)
    _segment(after, generations[split:], metric_name, rng, cfg, found, offset + split)


def _best_split(values: list[float], min_segment_length: int) -> tuple[int | None, float | None]:
    """Vectorized CUSUM-style scan over every candidate split point using
    prefix sums (O(n), not a per-split Python loop) — this runs inside
    the permutation loop in `_segment`, so its cost matters."""
    n = len(values)
    if n < 2 * min_segment_length:
        return None, None
    array = np.asarray(values, dtype=np.float64)
    cumsum = np.concatenate(([0.0], np.cumsum(array)))
    total = cumsum[-1]
    split_points = np.arange(min_segment_length, n - min_segment_length + 1)
    before_mean = cumsum[split_points] / split_points
    after_count = n - split_points
    after_mean = (total - cumsum[split_points]) / after_count
    statistics = np.abs(before_mean - after_mean) * np.sqrt(split_points * after_count / n)
    best_position = int(np.argmax(statistics))
    return int(split_points[best_position]), float(statistics[best_position])


_TRANSITION_LABELS: dict[str, tuple[str, str]] = {
    # metric_name -> (label when magnitude increases, label when magnitude decreases)
    "instantaneous_novelty": ("novelty_burst", "novelty_decline"),
    "mean_novelty": ("novelty_burst", "novelty_decline"),
    "genotypic_diversity": ("diversity_expansion", "diversity_collapse"),
    "behavioral_diversity": ("diversity_expansion", "diversity_collapse"),
    "fitness_mean": ("fitness_regime_change", "fitness_regime_change"),
    "learning_strategy_diversity": ("learning_strategy_turnover", "learning_strategy_turnover"),
    "evolvability": ("evolvability_increase", "evolvability_decrease"),
}


@dataclass(frozen=True)
class EvolutionaryTransitionRecord:
    """A structured, provenance-carrying record of one candidate
    evolutionary transition (Phase 9.8) — the unit Phase 10's discovery
    engine reads to formulate hypotheses."""

    experiment: str
    seed: int
    generation: int
    transition_type: str
    metric_evidence: ChangePoint
    lineages: tuple[int, ...] = ()
    strategy_clusters: tuple[int, ...] = ()
    configuration: dict[str, Any] = field(default_factory=dict)
    note: str = (
        "Candidate transition identified by statistical change-point detection. "
        "Not causally validated; requires further investigation (e.g. counterfactual "
        "analysis or a dedicated follow-up experiment)."
    )


def detect_regime_transitions(
    metric_series: Mapping[str, Sequence[float]],
    experiment: str,
    seed: int,
    rng: np.random.Generator,
    generations: Sequence[int] | None = None,
    config: ChangePointConfig | None = None,
    configuration: dict[str, Any] | None = None,
) -> list[EvolutionaryTransitionRecord]:
    """`metric_series` maps a metric name (any key from `_TRANSITION_LABELS`,
    or an arbitrary name — unrecognized names fall back to the generic
    `"regime_change"` label) to its per-generation values, e.g.
    `{"instantaneous_novelty": [...], "genotypic_diversity": [...]}`.
    Runs `detect_change_points` independently per metric — this function
    does not attempt joint multivariate change-point detection."""
    records: list[EvolutionaryTransitionRecord] = []
    for metric_name, values in metric_series.items():
        change_points = detect_change_points(
            values, metric_name, rng, generations=generations, config=config
        )
        increase_label, decrease_label = _TRANSITION_LABELS.get(
            metric_name, ("regime_change", "regime_change")
        )
        for cp in change_points:
            transition_type = increase_label if cp.magnitude > 0 else decrease_label
            records.append(
                EvolutionaryTransitionRecord(
                    experiment=experiment,
                    seed=seed,
                    generation=cp.generation,
                    transition_type=transition_type,
                    metric_evidence=cp,
                    configuration=dict(configuration or {}),
                )
            )
    records.sort(key=lambda r: r.generation)
    return records


__all__ = [
    "ChangePointConfig",
    "ChangePoint",
    "detect_change_points",
    "EvolutionaryTransitionRecord",
    "detect_regime_transitions",
]
