"""Summary statistics over a population's fitness scores.

This module summarizes fitness values that `genevra.evolution.fitness`
already computed — it does not decide what fitness means.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class FitnessSummary:
    n: int
    mean: float
    median: float
    max: float
    min: float
    std: float


def compute_fitness_summary(fitness_scores: Sequence[float]) -> FitnessSummary:
    if not fitness_scores:
        return FitnessSummary(n=0, mean=0.0, median=0.0, max=0.0, min=0.0, std=0.0)
    scores = np.asarray(fitness_scores, dtype=np.float64)
    return FitnessSummary(
        n=len(scores),
        mean=float(scores.mean()),
        median=float(np.median(scores)),
        max=float(scores.max()),
        min=float(scores.min()),
        std=float(scores.std()),
    )
