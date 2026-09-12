"""Phase 12.1: `OpenEndednessAnalyzer` — a modular measurement
architecture over the independent observables Phase 12.1 lists (change
potential, novelty potential, complexity potential, ecological potential,
innovation rate/persistence, diversity dynamics, evolutionary activity,
stagnation/recovery, lineage diversification, adaptive potential,
behavioral novelty, strategy-space expansion).

**These are not claimed to be equivalent aspects of one thing.** Each
measurement is independently enabled (`OpenEndednessAnalyzerConfig`) and
versioned (`MEASUREMENT_VERSIONS`) — this module composes existing,
already-tested analyzers (`genevra.analysis.open_endedness`,
`genevra.analysis.stagnation`, `genevra.innovation.events/activity/
trajectory`) rather than reimplementing any of them, and never reduces
its output to a single score or verdict.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any

import numpy as np

from genevra.analysis.open_endedness import OpenEndednessReport, build_open_endedness_report
from genevra.analysis.stagnation import StagnationAnalyzer, StagnationReport
from genevra.evolution.lineage import LineageEvent, LineageTracker
from genevra.innovation.activity import EvolutionaryActivityReport, build_activity_report
from genevra.innovation.events import InnovationEvent, detect_innovation_events
from genevra.innovation.trajectory import OpenEndednessTrajectoryReport, build_trajectory_report

MEASUREMENT_VERSIONS: dict[str, str] = {
    "base_open_endedness_proxies": "1.0",
    "innovation_events": "1.0",
    "evolutionary_activity": "1.0",
    "trajectory_shapes": "1.0",
}


@dataclass(frozen=True)
class OpenEndednessAnalyzerConfig:
    enable_innovation_events: bool = True
    enable_activity: bool = True
    enable_trajectory: bool = True
    innovation_z_threshold: float = 2.0
    innovation_min_cohort_size: int = 3
    n_strategy_clusters: int = 3


@dataclass(frozen=True)
class ExtendedOpenEndednessReport:
    """One independently-inspectable field per enabled measurement — a
    field is `None` exactly when that measurement was disabled or its
    prerequisite data was unavailable, never a fabricated default."""

    base: OpenEndednessReport
    stagnation: StagnationReport | None
    innovation_events: tuple[InnovationEvent, ...] | None
    activity: EvolutionaryActivityReport | None
    trajectory: OpenEndednessTrajectoryReport | None
    measurement_versions: dict[str, str] = field(default_factory=lambda: dict(MEASUREMENT_VERSIONS))
    note: str = (
        "Each field is an independent observable, not a component of one combined "
        "open-endedness score. No field here, alone or in combination, establishes that "
        "GENEVRA is 'open-ended' in any deeper theoretical sense — see "
        "genevra.innovation.report for the report that states this explicitly."
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "base": self.base.summary(),
            "stagnation": (
                {
                    "stagnation_score": self.stagnation.stagnation_score,
                    "contributing_signals": list(self.stagnation.contributing_signals),
                    "fitness_plateaued": self.stagnation.fitness_plateaued,
                    "detected_at_generation": self.stagnation.detected_at_generation,
                }
                if self.stagnation is not None
                else None
            ),
            "innovation_events": (
                [e.to_dict() for e in self.innovation_events]
                if self.innovation_events is not None
                else None
            ),
            "activity": self.activity.to_dict() if self.activity is not None else None,
            "trajectory": self.trajectory.to_dict() if self.trajectory is not None else None,
            "measurement_versions": self.measurement_versions,
            "note": self.note,
        }


class OpenEndednessAnalyzer:
    def __init__(self, config: OpenEndednessAnalyzerConfig | None = None) -> None:
        self._config = config if config is not None else OpenEndednessAnalyzerConfig()

    def analyze(
        self,
        trajectory: Sequence[Mapping[str, Any]],
        lineage_events: Sequence[LineageEvent],
        tracker: LineageTracker,
        rng: np.random.Generator,
        evolvability_trend_values: Sequence[float] | None = None,
    ) -> ExtendedOpenEndednessReport:
        cfg = self._config
        stagnation = StagnationAnalyzer().analyze(trajectory, evolvability_trend_values)
        base = build_open_endedness_report(trajectory, evolvability_trend_values, stagnation)

        innovation_events = None
        if cfg.enable_innovation_events:
            innovation_events = tuple(
                detect_innovation_events(
                    lineage_events,
                    tracker,
                    z_threshold=cfg.innovation_z_threshold,
                    min_cohort_size=cfg.innovation_min_cohort_size,
                )
            )

        activity = None
        if cfg.enable_activity and trajectory:
            activity = build_activity_report(
                trajectory, lineage_events, rng, n_strategy_clusters=cfg.n_strategy_clusters
            )

        trajectory_report = None
        if cfg.enable_trajectory and trajectory:
            metric_series = {
                "instantaneous_novelty": [float(g["instantaneous_novelty"]) for g in trajectory],
                "genotypic_diversity": [float(g["genotypic_diversity"]) for g in trajectory],
                "behavioral_diversity": [float(g["behavioral_diversity"]) for g in trajectory],
            }
            generations = [int(g["generation"]) for g in trajectory]
            trajectory_report = build_trajectory_report(metric_series, rng, generations=generations)

        return ExtendedOpenEndednessReport(
            base=base,
            stagnation=stagnation,
            innovation_events=innovation_events,
            activity=activity,
            trajectory=trajectory_report,
        )


__all__ = [
    "MEASUREMENT_VERSIONS",
    "OpenEndednessAnalyzerConfig",
    "ExtendedOpenEndednessReport",
    "OpenEndednessAnalyzer",
]
