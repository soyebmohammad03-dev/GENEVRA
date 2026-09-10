"""Phase 10.2: interpretable anomaly detection over evolutionary
trajectories, using robust (median/MAD-based) z-scores — no heavyweight
ML model, and every anomaly explains what changed, when, which metric,
how unusual it was (its z-score), and which experiment/seed produced it.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

import numpy as np

_MAD_TO_STD = 1.4826
"""Scales the median absolute deviation to be comparable to a standard
deviation under a normal distribution — the standard constant for robust
z-scores (see e.g. Iglewicz & Hoaglin's outlier-detection guidance)."""


@dataclass(frozen=True)
class Anomaly:
    experiment: str
    seed: int
    metric_name: str
    generation: int
    value: float
    robust_z_score: float
    baseline_median: float
    baseline_mad: float


def robust_z_scores(values: Sequence[float]) -> list[float]:
    """Median/MAD-based z-scores, with a standard-deviation fallback when
    the MAD itself is zero (a majority-constant series, e.g. many equal
    values plus a single spike, where the median absolute deviation is
    trivially 0 even though the series is not actually constant) — the
    standard remedy for that known MAD degeneracy, since scale-free
    outlier detection is otherwise undefined there."""
    array = np.asarray(values, dtype=np.float64)
    median = float(np.median(array))
    mad = float(np.median(np.abs(array - median)))
    scale = mad * _MAD_TO_STD
    if scale == 0.0:
        std = float(np.std(array))
        if std == 0.0:
            return [0.0] * len(array)
        scale = std
    return [float((x - median) / scale) for x in array]


def detect_anomalies(
    metric_series: Mapping[str, Sequence[float]],
    experiment: str,
    seed: int,
    generations: Sequence[int] | None = None,
    z_threshold: float = 3.5,
) -> list[Anomaly]:
    """One `Anomaly` per (metric, generation) whose robust z-score exceeds
    `z_threshold` in absolute value. `z_threshold=3.5` is Iglewicz &
    Hoaglin's commonly cited modified-z-score cutoff, exposed as a
    parameter rather than buried."""
    anomalies: list[Anomaly] = []
    for metric_name, values in metric_series.items():
        if len(values) < 2:
            continue
        gens = list(generations) if generations is not None else list(range(len(values)))
        array = np.asarray(values, dtype=np.float64)
        median = float(np.median(array))
        mad = float(np.median(np.abs(array - median)))
        scores = robust_z_scores(values)
        for generation, value, score in zip(gens, values, scores, strict=True):
            if abs(score) >= z_threshold:
                anomalies.append(
                    Anomaly(
                        experiment=experiment,
                        seed=seed,
                        metric_name=metric_name,
                        generation=generation,
                        value=float(value),
                        robust_z_score=score,
                        baseline_median=median,
                        baseline_mad=mad,
                    )
                )
    anomalies.sort(key=lambda a: a.generation)
    return anomalies


def trajectory_metric_series(
    trajectory: Sequence[Mapping[str, Any]], metric_keys: Sequence[str]
) -> dict[str, list[float]]:
    """Extracts named per-generation series from a `Trajectory.to_dict()`-
    shaped sequence, for feeding into `detect_anomalies` or
    `genevra.analysis.regime_detection`. `metric_keys` entries containing
    a dot (e.g. `"fitness_summary.mean"`) index into a nested dict."""
    series: dict[str, list[float]] = {}
    for key in metric_keys:
        parts = key.split(".")
        values = []
        for generation in trajectory:
            node: Any = generation
            for part in parts:
                node = node[part]
            values.append(float(node))
        series[key] = values
    return series


__all__ = ["Anomaly", "robust_z_scores", "detect_anomalies", "trajectory_metric_series"]
