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


@dataclass(frozen=True)
class EffectSizeResult:
    """Cohen's d (pooled-standard-deviation standardized mean
    difference) between two independent samples — a magnitude measure,
    deliberately reported alongside (never instead of) `permutation_test`'s
    p-value: a p-value says whether a difference is unlikely to be chance
    given the sample size, an effect size says how large the difference
    actually is, and conflating the two is a common misreading Phase
    8.14 explicitly avoids by keeping them as separate fields, computed
    by separate functions."""

    cohens_d: float
    mean_difference: float
    pooled_std: float
    n_a: int
    n_b: int


def cohens_d(sample_a: Sequence[float], sample_b: Sequence[float]) -> EffectSizeResult:
    a = np.asarray(sample_a, dtype=np.float64)
    b = np.asarray(sample_b, dtype=np.float64)
    if len(a) < 2 or len(b) < 2:
        raise ValueError("cohens_d requires at least 2 observations per sample")
    mean_difference = float(a.mean() - b.mean())
    pooled_variance = ((len(a) - 1) * a.var(ddof=1) + (len(b) - 1) * b.var(ddof=1)) / (
        len(a) + len(b) - 2
    )
    pooled_std = float(np.sqrt(pooled_variance))
    d = mean_difference / pooled_std if pooled_std > 0 else float("nan")
    return EffectSizeResult(
        cohens_d=d, mean_difference=mean_difference, pooled_std=pooled_std, n_a=len(a), n_b=len(b)
    )


@dataclass(frozen=True)
class BootstrapCI:
    """A percentile-bootstrap confidence interval for the mean of one
    sample — the resampling-based analog of `aggregate_metric_across_runs`'s
    percentile spread, for a single scalar (e.g. one condition's final-
    generation fitness across seeds) rather than a per-generation series.
    Explicitly not a normal-approximation CI (see this module's
    docstring on why that assumption isn't justified at typical
    GENEVRA seed counts)."""

    point_estimate: float
    low: float
    high: float
    confidence_level: float
    n_resamples: int
    n_observations: int


def bootstrap_confidence_interval(
    sample: Sequence[float],
    rng: np.random.Generator,
    confidence_level: float = 0.90,
    n_resamples: int = 2000,
) -> BootstrapCI:
    if not 0.0 < confidence_level < 1.0:
        raise ValueError("confidence_level must be in (0, 1)")
    values = np.asarray(sample, dtype=np.float64)
    n = len(values)
    if n < 2:
        raise ValueError("bootstrap_confidence_interval requires at least 2 observations")
    resample_means = np.empty(n_resamples, dtype=np.float64)
    for i in range(n_resamples):
        resample_means[i] = rng.choice(values, size=n, replace=True).mean()
    alpha = 1.0 - confidence_level
    low, high = np.percentile(resample_means, [100 * alpha / 2, 100 * (1 - alpha / 2)])
    return BootstrapCI(
        point_estimate=float(values.mean()),
        low=float(low),
        high=float(high),
        confidence_level=confidence_level,
        n_resamples=n_resamples,
        n_observations=n,
    )
