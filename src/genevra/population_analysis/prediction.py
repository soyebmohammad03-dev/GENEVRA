"""Phase 16.4: does a current metric predict a future one?

Every within-run correlation here is *descriptive*, not inferential:
generations within one seed's trajectory are autocorrelated (the same
caveat `genevra.innovation.activity` already documents for per-generation
values), so a single seed's lag-k Pearson r is reported as one data
point, never as if it alone were a statistically independent finding.
The actual inferential claim is the *distribution of that r across
independent seeds* — seed is the unit of replication here too.
"""

from __future__ import annotations

import dataclasses
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

import numpy as np

from genevra.analysis.aggregation import BootstrapCI, bootstrap_confidence_interval


def lagged_pairs(series: Sequence[float], lag: int) -> tuple[list[float], list[float]]:
    """`(x[:-lag], x[lag:])`-style pairing for `x -> x_future`
    association within one trajectory."""
    if lag <= 0:
        raise ValueError("lag must be positive")
    if len(series) <= lag:
        return [], []
    return list(series[:-lag]), list(series[lag:])


def within_seed_lagged_correlation(
    predictor: Sequence[float], outcome: Sequence[float], lag: int
) -> float | None:
    """Pearson r between `predictor[t]` and `outcome[t+lag]` within one
    seed's trajectory. `None` if fewer than 3 pairs remain or either
    series is constant. Descriptive only — see module docstring."""
    x, _ = lagged_pairs(predictor, lag)
    _, y = lagged_pairs(outcome, lag)
    n = min(len(x), len(y))
    if n < 3:
        return None
    a, b = np.asarray(x[:n]), np.asarray(y[:n])
    if np.std(a) == 0.0 or np.std(b) == 0.0:
        return None
    return float(np.corrcoef(a, b)[0, 1])


@dataclass(frozen=True)
class LaggedPredictionResult:
    lag: int
    n_seeds: int
    per_seed_correlation: dict[int, float]
    mean_correlation: float | None
    bootstrap_ci: BootstrapCI | None
    """Bootstrap CI on the *distribution of per-seed correlation
    coefficients* — the seed-level inferential step this module adds on
    top of each individually-descriptive within-seed r."""

    def to_dict(self) -> dict[str, Any]:
        return {
            "lag": self.lag,
            "n_seeds": self.n_seeds,
            "per_seed_correlation": self.per_seed_correlation,
            "mean_correlation": self.mean_correlation,
            "bootstrap_ci": dataclasses.asdict(self.bootstrap_ci) if self.bootstrap_ci else None,
        }


def test_lagged_prediction(
    predictor_by_seed: Mapping[int, Sequence[float]],
    outcome_by_seed: Mapping[int, Sequence[float]],
    lag: int,
    rng: np.random.Generator,
) -> LaggedPredictionResult:
    shared_seeds = sorted(set(predictor_by_seed) & set(outcome_by_seed))
    per_seed: dict[int, float] = {}
    for seed in shared_seeds:
        r = within_seed_lagged_correlation(predictor_by_seed[seed], outcome_by_seed[seed], lag)
        if r is not None:
            per_seed[seed] = r
    values = list(per_seed.values())
    ci = bootstrap_confidence_interval(values, rng) if len(values) >= 2 else None
    return LaggedPredictionResult(
        lag=lag,
        n_seeds=len(per_seed),
        per_seed_correlation=per_seed,
        mean_correlation=float(np.mean(values)) if values else None,
        bootstrap_ci=ci,
    )


__all__ = [
    "lagged_pairs",
    "within_seed_lagged_correlation",
    "LaggedPredictionResult",
    "test_lagged_prediction",
]
