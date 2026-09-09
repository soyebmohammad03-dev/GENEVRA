"""Descriptive aggregation across multiple runs (seeds/conditions), and a
small non-parametric test for comparing two conditions.

Statistical integrity constraints followed throughout this module:

- Everything here is a **descriptive** summary (mean/median/std/percentile
  spread) except `permutation_test`, which is the one **inferential**
  method provided — and it is a real, computed permutation test, not a
  fabricated p-value.
- No parametric confidence interval is computed. With the small run
  counts (a handful of seeds) GENEVRA experiments realistically use, a
  normal-approximation CI's assumptions are not justified; a percentile
  spread across the actual runs is reported instead, labeled as exactly
  that.
- Runs of different lengths (a run that hit extinction early has a
  shorter trajectory) are never padded or silently dropped: aggregation
  is done per-generation over however many runs actually have data at
  that generation (`n_runs`, which can shrink across the x-axis) — the
  data available is used, but the fact that it's shrinking is not hidden.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from typing import Any

import numpy as np


@dataclass(frozen=True)
class MetricAggregate:
    generation: int
    n_runs: int
    mean: float
    median: float
    std: float
    percentile_low: float
    percentile_high: float


def aggregate_metric_across_runs(
    trajectories: Sequence[Sequence[Mapping[str, Any]]],
    extract: Callable[[Mapping[str, Any]], float],
    percentile_bounds: tuple[float, float] = (10.0, 90.0),
) -> list[MetricAggregate]:
    """One `MetricAggregate` per generation index present in *any* run,
    computed over whichever runs still have data at that generation."""
    max_length = max((len(trajectory) for trajectory in trajectories), default=0)
    aggregates: list[MetricAggregate] = []
    for generation in range(max_length):
        values = [
            extract(trajectory[generation])
            for trajectory in trajectories
            if len(trajectory) > generation
        ]
        if not values:
            continue
        array = np.asarray(values, dtype=np.float64)
        low, high = np.percentile(array, percentile_bounds)
        aggregates.append(
            MetricAggregate(
                generation=generation,
                n_runs=len(values),
                mean=float(array.mean()),
                median=float(np.median(array)),
                std=float(array.std()),
                percentile_low=float(low),
                percentile_high=float(high),
            )
        )
    return aggregates


def final_generation_values(
    trajectories: Sequence[Sequence[Mapping[str, Any]]],
    extract: Callable[[Mapping[str, Any]], float],
) -> list[float]:
    """The last *available* generation's value for each non-empty
    trajectory — a run that went extinct early is represented by its
    actual final state, not excluded or padded to a common length."""
    return [extract(trajectory[-1]) for trajectory in trajectories if trajectory]


def area_under_trajectory(values: Sequence[float]) -> float:
    """Trapezoidal-rule area under a sequence of per-generation values
    (unit generation spacing) — a compact single-number summary of a
    whole trajectory, e.g. "total novelty accumulated over the run,"
    without needing a plot to compare two runs."""
    if len(values) < 2:
        return 0.0
    array = np.asarray(values, dtype=np.float64)
    return float(np.sum((array[:-1] + array[1:]) / 2.0))


@dataclass(frozen=True)
class PermutationTestResult:
    observed_difference: float
    p_value: float
    num_permutations: int


def permutation_test(
    sample_a: Sequence[float],
    sample_b: Sequence[float],
    rng: np.random.Generator,
    num_permutations: int = 2000,
) -> PermutationTestResult:
    """A two-sided permutation test for a difference in means between two
    independent samples: shuffle the pooled labels `num_permutations`
    times and ask how often a difference at least as extreme as the
    observed one occurs by chance. Appropriate for small, non-normal
    samples (a handful of experiment seeds) where a t-test's normality
    assumption would not be justified — the standard non-parametric
    alternative in that setting."""
    a = np.asarray(sample_a, dtype=np.float64)
    b = np.asarray(sample_b, dtype=np.float64)
    if len(a) == 0 or len(b) == 0:
        raise ValueError("both samples must be non-empty")
    observed = float(a.mean() - b.mean())
    pooled = np.concatenate([a, b])
    n_a = len(a)
    count_at_least_as_extreme = 0
    for _ in range(num_permutations):
        rng.shuffle(pooled)
        permuted_difference = pooled[:n_a].mean() - pooled[n_a:].mean()
        if abs(permuted_difference) >= abs(observed):
            count_at_least_as_extreme += 1
    # +1/+1 smoothing: a permutation p-value is never exactly zero, since
    # the observed arrangement is itself one of the permutations.
    p_value = (count_at_least_as_extreme + 1) / (num_permutations + 1)
    return PermutationTestResult(
        observed_difference=observed, p_value=p_value, num_permutations=num_permutations
    )
