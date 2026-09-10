"""Phase 10.3: correlation discovery across experiments.

**Unit of analysis.** Every function here operates on one row per
*(experiment, seed) run* — a single scalar summary per variable per run
(e.g. final-generation fitness, or `area_under_trajectory` novelty) —
never on raw per-generation values pooled across a run. Treating
thousands of generations from one run as thousands of independent
samples would be pseudoreplication: generations within a single run are
highly autocorrelated, not independent observations. `RunSummary` makes
this unit explicit; nothing in this module accepts a bare trajectory.

Correlations are Spearman rank correlation (robust to the non-linear,
non-normal relationships common in evolutionary trajectories), each with
a permutation-test p-value — not a parametric p-value whose normality
assumption would not be justified at typical seed counts (same rationale
as `genevra.analysis.aggregation.permutation_test`). Because this module
is meant to scan many variable pairs at once, callers should feed its
p-values through `genevra.discovery.multiple_testing.benjamini_hochberg`
before treating any of them as noteworthy.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass

import numpy as np
import numpy.typing as npt

_FloatSequence = Sequence[float] | npt.NDArray[np.float64]


@dataclass(frozen=True)
class RunSummary:
    """One row of the unit of analysis this module requires: a single
    experiment/seed run, reduced to scalar variables."""

    experiment: str
    seed: int
    variables: Mapping[str, float]


@dataclass(frozen=True)
class CorrelationResult:
    variable_a: str
    variable_b: str
    spearman_rho: float
    p_value: float
    n_runs: int
    unit_of_analysis: str = "one (experiment, seed) run per observation"


def _rank(values: _FloatSequence) -> np.ndarray:
    """Average ranks (ties share the mean rank of their tied block) —
    the standard input transform for Spearman correlation."""
    array = np.asarray(values, dtype=np.float64)
    order = np.argsort(array, kind="mergesort")
    sorted_values = array[order]
    ranks = np.empty(len(array), dtype=np.float64)
    i = 0
    while i < len(array):
        j = i
        while j + 1 < len(array) and sorted_values[j + 1] == sorted_values[i]:
            j += 1
        ranks[order[i : j + 1]] = (i + 1 + j + 1) / 2.0
        i = j + 1
    return ranks


def _pearson(x: np.ndarray, y: np.ndarray) -> float:
    if np.std(x) == 0.0 or np.std(y) == 0.0:
        return 0.0
    return float(np.corrcoef(x, y)[0, 1])


def spearman_rho(x: _FloatSequence, y: _FloatSequence) -> float:
    if len(x) != len(y):
        raise ValueError("x and y must be the same length")
    return _pearson(_rank(x), _rank(y))


def correlation_discovery(
    runs: Sequence[RunSummary],
    variable_pairs: Sequence[tuple[str, str]],
    rng: np.random.Generator,
    num_permutations: int = 1000,
) -> list[CorrelationResult]:
    """For each requested `(variable_a, variable_b)` pair, computes
    Spearman rho over every run that has both variables defined, with a
    permutation-test p-value (shuffle one side, recompute rho,
    `num_permutations` times). Runs missing either variable are excluded
    for that pair only — never dropped from other pairs."""
    results = []
    for variable_a, variable_b in variable_pairs:
        paired = [
            (r.variables[variable_a], r.variables[variable_b])
            for r in runs
            if variable_a in r.variables and variable_b in r.variables
        ]
        if len(paired) < 3:
            results.append(
                CorrelationResult(
                    variable_a=variable_a,
                    variable_b=variable_b,
                    spearman_rho=0.0,
                    p_value=1.0,
                    n_runs=len(paired),
                )
            )
            continue
        x = np.array([p[0] for p in paired], dtype=np.float64)
        y = np.array([p[1] for p in paired], dtype=np.float64)
        observed = spearman_rho(x, y)

        shuffled_y = y.copy()
        count_at_least_as_extreme = 0
        for _ in range(num_permutations):
            rng.shuffle(shuffled_y)
            permuted_rho = spearman_rho(x, shuffled_y)
            if abs(permuted_rho) >= abs(observed):
                count_at_least_as_extreme += 1
        p_value = (count_at_least_as_extreme + 1) / (num_permutations + 1)

        results.append(
            CorrelationResult(
                variable_a=variable_a,
                variable_b=variable_b,
                spearman_rho=observed,
                p_value=p_value,
                n_runs=len(paired),
            )
        )
    return results


__all__ = ["RunSummary", "CorrelationResult", "spearman_rho", "correlation_discovery"]
