"""Phase 16.2: population-level robustness, built on Phase 13's
per-genotype `RobustnessAnalyzer` plus this package's seed-as-unit
aggregation layer.

Callers are expected to have already run `RobustnessAnalyzer.analyze()`
once per seed (typically on a representative or sampled genome from that
seed's final population) and pass in the resulting per-seed
`RobustnessProfile.genetic.mean` (or another dimension) values. This
module does not re-run the perturbation sampling itself — that stays
Phase 13's job — it only aggregates across seeds correctly.
"""

from __future__ import annotations

import dataclasses
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

import numpy as np

from genevra.analysis.aggregation import BootstrapCI, bootstrap_confidence_interval
from genevra.population_analysis.aggregation import to_condition_sample


@dataclass(frozen=True)
class PopulationRobustnessSummary:
    n_seeds: int
    mean: float | None
    median: float | None
    between_seed_variance: float | None
    """Variance of the per-seed robustness values themselves — how much
    robustness differs from one independent run to another."""
    bootstrap_ci: BootstrapCI | None

    def to_dict(self) -> dict[str, Any]:
        return {
            "n_seeds": self.n_seeds,
            "mean": self.mean,
            "median": self.median,
            "between_seed_variance": self.between_seed_variance,
            "bootstrap_ci": dataclasses.asdict(self.bootstrap_ci) if self.bootstrap_ci else None,
        }


class PopulationRobustnessAnalyzer:
    def summarize(
        self, robustness_mean_by_seed: Mapping[int, float], rng: np.random.Generator
    ) -> PopulationRobustnessSummary:
        if not robustness_mean_by_seed:
            return PopulationRobustnessSummary(0, None, None, None, None)
        sample = to_condition_sample(robustness_mean_by_seed)
        ci = bootstrap_confidence_interval(sample, rng) if len(sample) >= 2 else None
        return PopulationRobustnessSummary(
            n_seeds=len(sample),
            mean=float(np.mean(sample)),
            median=float(np.median(sample)),
            between_seed_variance=float(np.var(sample, ddof=1)) if len(sample) >= 2 else None,
            bootstrap_ci=ci,
        )


def robustness_metric_association(
    robustness_by_seed: Mapping[int, float], other_metric_by_seed: Mapping[int, float]
) -> float | None:
    """Pearson correlation between per-seed robustness and any other
    per-seed metric (evolvability, diversity, innovation rate,
    environmental volatility, ...), computed at the seed level only.
    `None` if fewer than 3 shared seeds or either series is constant —
    the same convention as `genevra.mechanisms.robustness.
    robustness_evolvability_association`, extended from per-genotype to
    per-seed values."""
    shared_seeds = sorted(set(robustness_by_seed) & set(other_metric_by_seed))
    if len(shared_seeds) < 3:
        return None
    a = np.array([robustness_by_seed[s] for s in shared_seeds])
    b = np.array([other_metric_by_seed[s] for s in shared_seeds])
    if np.std(a) == 0.0 or np.std(b) == 0.0:
        return None
    return float(np.corrcoef(a, b)[0, 1])


__all__ = [
    "PopulationRobustnessSummary",
    "PopulationRobustnessAnalyzer",
    "robustness_metric_association",
]
