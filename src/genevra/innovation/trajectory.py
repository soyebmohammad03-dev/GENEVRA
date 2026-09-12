"""Phase 12.7: open-endedness trajectory analysis.

Classifies each tracked metric's trajectory shape using the same
change-point machinery already in `genevra.analysis.regime_detection`
(never a second, unexplained smoothing/fit) plus a plain linear trend —
and only ever with the cautious vocabulary Phase 12.7 requires. No shape
label here is, or implies, "proven open-ended": `TrajectoryShape` values
describe the *observed, finite* series only.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any, Literal

import numpy as np

from genevra.analysis.regime_detection import ChangePoint, ChangePointConfig, detect_change_points
from genevra.analysis.stagnation import _trend_slope

TrajectoryShape = Literal[
    "sustained_increase", "sustained_decrease", "plateau", "oscillating", "regime_shift"
]

_SHAPE_NOTES: dict[str, str] = {
    "sustained_increase": "sustained increase observed within the tested horizon — not "
    "evidence of unbounded increase or 'proven open-ended' growth",
    "sustained_decrease": "sustained decrease observed within the tested horizon",
    "plateau": "no evidence of continued change within the tested horizon (finite-run "
    "proxy only — a longer run could still resume changing)",
    "oscillating": "the trend reverses sign repeatedly; evidence consistent with a "
    "cyclical or unstable regime, not a monotonic trajectory",
    "regime_shift": "one or more statistically detected change points partition this "
    "metric into distinct segments (see change_points) — a candidate discontinuity, "
    "not a confirmed discrete event",
}


@dataclass(frozen=True)
class MetricTrajectorySummary:
    metric_name: str
    shape: TrajectoryShape
    slope: float
    change_points: tuple[ChangePoint, ...]
    interpretation_note: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "metric_name": self.metric_name,
            "shape": self.shape,
            "slope": self.slope,
            "n_change_points": len(self.change_points),
            "change_point_generations": [cp.generation for cp in self.change_points],
            "interpretation_note": self.interpretation_note,
        }


def classify_metric_trajectory(
    values: Sequence[float],
    metric_name: str,
    rng: np.random.Generator,
    generations: Sequence[int] | None = None,
    flat_threshold: float = 0.01,
    change_point_config: ChangePointConfig | None = None,
) -> MetricTrajectorySummary:
    if len(values) < 2:
        return MetricTrajectorySummary(
            metric_name=metric_name,
            shape="plateau",
            slope=0.0,
            change_points=(),
            interpretation_note=_SHAPE_NOTES["plateau"],
        )

    change_points = detect_change_points(
        values, metric_name, rng, generations=generations, config=change_point_config
    )
    slope = _trend_slope(values)

    if change_points:
        shape: TrajectoryShape = "regime_shift"
    elif abs(slope) <= flat_threshold:
        shape = "plateau"
    elif slope > 0:
        shape = "sustained_increase"
    else:
        shape = "sustained_decrease"

    if shape in ("sustained_increase", "sustained_decrease") and _oscillates(values):
        shape = "oscillating"

    return MetricTrajectorySummary(
        metric_name=metric_name,
        shape=shape,
        slope=slope,
        change_points=tuple(change_points),
        interpretation_note=_SHAPE_NOTES[shape],
    )


def _oscillates(values: Sequence[float], window: int = 5, min_sign_changes: int = 2) -> bool:
    """Same windowed-slope sign-change heuristic as
    `genevra.discovery.phenomena.RepeatedRegimeRule` — reused by
    definition, not reimplemented independently, to keep "oscillating"
    meaning one thing across this codebase."""
    if len(values) < window * 2:
        return False
    slopes = [
        _trend_slope(values[i : i + window]) for i in range(0, len(values) - window + 1, window)
    ]
    signs = [1 if s > 0 else (-1 if s < 0 else 0) for s in slopes if s != 0]
    sign_changes = sum(1 for a, b in zip(signs, signs[1:], strict=False) if a != b)
    return sign_changes >= min_sign_changes


@dataclass(frozen=True)
class OpenEndednessTrajectoryReport:
    metric_summaries: tuple[MetricTrajectorySummary, ...]
    note: str = field(
        default=(
            "Every shape label describes the observed, finite trajectory only. "
            "'sustained_increase' never implies unbounded growth or that a system has "
            "been proven open-ended; 'plateau' never implies the system could not "
            "resume producing change under further generations or a different "
            "environment."
        )
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "metric_summaries": [s.to_dict() for s in self.metric_summaries],
            "note": self.note,
        }


def build_trajectory_report(
    metric_series: Mapping[str, Sequence[float]],
    rng: np.random.Generator,
    generations: Sequence[int] | None = None,
) -> OpenEndednessTrajectoryReport:
    summaries = tuple(
        classify_metric_trajectory(values, name, rng, generations=generations)
        for name, values in metric_series.items()
    )
    return OpenEndednessTrajectoryReport(metric_summaries=summaries)


__all__ = [
    "TrajectoryShape",
    "MetricTrajectorySummary",
    "classify_metric_trajectory",
    "OpenEndednessTrajectoryReport",
    "build_trajectory_report",
]
