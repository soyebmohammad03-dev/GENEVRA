"""Phase 8.11: an explicit suite of open-endedness *proxies*, never a
verdict.

GENEVRA does not claim to solve, or even fully operationalize, the
definition of open-ended evolution — that is an unresolved question in
the field, not a bug to fix here. What this module does is assemble the
measurements GENEVRA already computes elsewhere (novelty, diversity,
stagnation, evolvability trend) into one `OpenEndednessReport`, each
dimension kept independently inspectable. It never emits a single
"OPEN_ENDED = True/False" verdict — `summary()` returns per-dimension
trajectory descriptions and explicit evidence limitations; the
scientific interpretation is left to the researcher reading the report.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any

from genevra.analysis.aggregation import area_under_trajectory
from genevra.analysis.stagnation import StagnationReport, _trend_slope

_LIMITATION_NOTE = (
    "This report assembles measurable proxies (continued novelty generation, "
    "genotypic/behavioral diversity, cumulative evolutionary change, evolvability "
    "trend, stagnation indicators) over the observed run only. It does not, and "
    "cannot, establish that a system is 'open-ended' in any deeper theoretical "
    "sense: a finite run showing sustained novelty so far is not proof novelty "
    "generation would continue indefinitely, and the reverse (a run that looks "
    "stagnant late) is not proof the system could never resume producing novelty "
    "under different conditions. Treat every field as one data point, not a verdict."
)


@dataclass(frozen=True)
class TrendDescription:
    """A plain linear-trend description of one metric's trajectory —
    deliberately the same transparent method `genevra.analysis.stagnation`
    already uses, not a different, unexplained smoothing or fit."""

    metric_name: str
    n_generations: int
    start_value: float
    end_value: float
    slope: float
    increasing: bool


@dataclass(frozen=True)
class OpenEndednessReport:
    novelty_trend: TrendDescription
    genotypic_diversity_trend: TrendDescription
    behavioral_diversity_trend: TrendDescription
    evolvability_trend: TrendDescription | None
    stagnation: StagnationReport | None
    cumulative_novelty_area: float
    limitation_note: str = field(default=_LIMITATION_NOTE)

    def summary(self) -> dict[str, Any]:
        """A structured dict, not prose — no automatic
        "OPEN_ENDED = True/False" claim is ever produced here."""
        return {
            "novelty_trend": self.novelty_trend,
            "genotypic_diversity_trend": self.genotypic_diversity_trend,
            "behavioral_diversity_trend": self.behavioral_diversity_trend,
            "evolvability_trend": self.evolvability_trend,
            "stagnation_detected": (
                self.stagnation.stagnation_score >= 0.5 if self.stagnation else None
            ),
            "cumulative_novelty_area": self.cumulative_novelty_area,
            "limitation_note": self.limitation_note,
        }


def _trend(name: str, values: Sequence[float]) -> TrendDescription:
    if len(values) < 2:
        return TrendDescription(
            metric_name=name,
            n_generations=len(values),
            start_value=float(values[0]) if values else 0.0,
            end_value=float(values[0]) if values else 0.0,
            slope=0.0,
            increasing=False,
        )
    slope = _trend_slope(values)
    return TrendDescription(
        metric_name=name,
        n_generations=len(values),
        start_value=float(values[0]),
        end_value=float(values[-1]),
        slope=slope,
        increasing=slope > 0.0,
    )


def build_open_endedness_report(
    trajectory: Sequence[Mapping[str, Any]],
    evolvability_trend_values: Sequence[float] | None = None,
    stagnation: StagnationReport | None = None,
) -> OpenEndednessReport:
    """`trajectory` is `Trajectory.to_dict()`-shaped. `evolvability_trend_values`,
    when given, should come from a separate `sample_evolvability_over_generations`
    run (see `genevra.analysis.evolvability_over_time`) — this function does
    not compute evolvability itself."""
    novelty_values = [float(g["instantaneous_novelty"]) for g in trajectory]
    genotypic_values = [float(g["genotypic_diversity"]) for g in trajectory]
    behavioral_values = [float(g["behavioral_diversity"]) for g in trajectory]

    evolvability_trend = (
        _trend("evolvability", evolvability_trend_values) if evolvability_trend_values else None
    )

    return OpenEndednessReport(
        novelty_trend=_trend("instantaneous_novelty", novelty_values),
        genotypic_diversity_trend=_trend("genotypic_diversity", genotypic_values),
        behavioral_diversity_trend=_trend("behavioral_diversity", behavioral_values),
        evolvability_trend=evolvability_trend,
        stagnation=stagnation,
        cumulative_novelty_area=area_under_trajectory(novelty_values),
    )
