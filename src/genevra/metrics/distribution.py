"""A generic population-level distribution summary — mean/std alone can
hide a genuinely bimodal population (e.g. two co-existing learning
strategies, one high-plasticity and one low-plasticity), so this reports
quantiles too rather than collapsing a distribution to one number.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class DistributionSummary:
    n: int
    mean: float
    std: float
    median: float
    q25: float
    q75: float
    min: float
    max: float


def summarize_distribution(values: Sequence[float]) -> DistributionSummary:
    if not values:
        return DistributionSummary(
            n=0, mean=0.0, std=0.0, median=0.0, q25=0.0, q75=0.0, min=0.0, max=0.0
        )
    array = np.asarray(values, dtype=np.float64)
    q25, median, q75 = np.percentile(array, [25.0, 50.0, 75.0])
    return DistributionSummary(
        n=len(array),
        mean=float(array.mean()),
        std=float(array.std()),
        median=float(median),
        q25=float(q25),
        q75=float(q75),
        min=float(array.min()),
        max=float(array.max()),
    )
