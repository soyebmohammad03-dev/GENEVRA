"""An initial, explicitly-thresholded evolutionary stagnation detector.

**Fitness plateau is not evolutionary stagnation.** A population can stop
increasing in fitness while continuing to explore genuinely novel
behaviors — or it can keep a flat fitness trajectory purely because the
fitness function has saturated, with no bearing on whether the population
is still evolving interesting variation. `StagnationAnalyzer` computes
`fitness_plateaued` as one piece of *contextual* information, but it is
structurally excluded from `stagnation_score` and `contributing_signals`
— it can never, on its own, cause a stagnation detection, and no code
path in this module adds it to the combined score. This split is tested
directly in `tests/test_stagnation.py`.

The actual signals combined into `stagnation_score` are trend-based:
whether behavioral novelty, genotypic diversity, behavioral diversity,
and (optionally, if supplied) evolvability are declining over a trailing
window of generations. `stagnation_score` is a simple, transparent
fraction — the count of triggered signals divided by the count of signals
actually evaluated — not a validated statistical model of "how stagnant"
a population is. Every threshold used is an explicit field on
`StagnationConfig`, not a constant buried in a function body.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

import numpy as np


@dataclass(frozen=True)
class StagnationConfig:
    window: int = 5
    novelty_decline_threshold: float = -0.01
    genotypic_diversity_decline_threshold: float = -0.01
    behavioral_diversity_decline_threshold: float = -0.01
    evolvability_decline_threshold: float = -0.01
    fitness_plateau_threshold: float = 0.05
    min_signal_fraction_to_detect: float = 0.5

    def __post_init__(self) -> None:
        if self.window < 2:
            raise ValueError("window must be >= 2 to compute a trend")
        if not 0.0 <= self.min_signal_fraction_to_detect <= 1.0:
            raise ValueError("min_signal_fraction_to_detect must be in [0, 1]")


@dataclass(frozen=True)
class StagnationReport:
    stagnation_score: float
    contributing_signals: tuple[str, ...]
    signals_evaluated: tuple[str, ...]
    detected_at_generation: int | None
    fitness_plateaued: bool
    note: str = (
        "stagnation_score combines declining-trend signals (novelty, "
        "genotypic diversity, behavioral diversity, evolvability where "
        "available) over a trailing window. fitness_plateaued is reported "
        "separately and is never included in stagnation_score or "
        "contributing_signals: a fitness plateau alone is not evolutionary "
        "stagnation, since a population can continue producing novel "
        "behavior without its fitness increasing."
    )


class StagnationAnalyzer:
    def __init__(self, config: StagnationConfig | None = None) -> None:
        self._config = config if config is not None else StagnationConfig()

    def analyze(
        self,
        trajectory: Sequence[Mapping[str, Any]],
        evolvability_trend: Sequence[float] | None = None,
    ) -> StagnationReport:
        """`trajectory` is a sequence of `GenerationSnapshot`-shaped dicts
        (as produced by `Trajectory.to_dict()`), evaluated over its
        trailing `config.window` generations. `evolvability_trend`, if
        given, is a separately-supplied series of evolvability
        measurements (e.g. from `evolvability_over_time`) aligned to the
        same trailing window — evolvability is not computed by this
        analyzer, since that requires running `EvolvabilityAnalyzer`
        against the population, an on-demand cost this module does not
        incur on its own."""
        cfg = self._config
        window = trajectory[-cfg.window :] if len(trajectory) >= cfg.window else list(trajectory)

        signals_evaluated: list[str] = []
        contributing: list[str] = []

        if len(window) >= 2:
            self._check_decline(
                [float(g["instantaneous_novelty"]) for g in window],
                cfg.novelty_decline_threshold,
                "declining_novelty",
                signals_evaluated,
                contributing,
            )
            self._check_decline(
                [float(g["genotypic_diversity"]) for g in window],
                cfg.genotypic_diversity_decline_threshold,
                "declining_genotypic_diversity",
                signals_evaluated,
                contributing,
            )
            self._check_decline(
                [float(g["behavioral_diversity"]) for g in window],
                cfg.behavioral_diversity_decline_threshold,
                "declining_behavioral_diversity",
                signals_evaluated,
                contributing,
            )

        if evolvability_trend is not None and len(evolvability_trend) >= 2:
            self._check_decline(
                list(evolvability_trend),
                cfg.evolvability_decline_threshold,
                "declining_evolvability",
                signals_evaluated,
                contributing,
            )

        fitness_plateaued = False
        if len(window) >= 2:
            fitness_slope = _trend_slope([float(g["fitness_summary"]["mean"]) for g in window])
            fitness_plateaued = abs(fitness_slope) < cfg.fitness_plateau_threshold

        stagnation_score = len(contributing) / len(signals_evaluated) if signals_evaluated else 0.0
        detected_at_generation = None
        if stagnation_score >= cfg.min_signal_fraction_to_detect and trajectory:
            detected_at_generation = int(trajectory[-1]["generation"])

        return StagnationReport(
            stagnation_score=stagnation_score,
            contributing_signals=tuple(contributing),
            signals_evaluated=tuple(signals_evaluated),
            detected_at_generation=detected_at_generation,
            fitness_plateaued=fitness_plateaued,
        )

    @staticmethod
    def _check_decline(
        values: list[float],
        threshold: float,
        signal_name: str,
        signals_evaluated: list[str],
        contributing: list[str],
    ) -> None:
        signals_evaluated.append(signal_name)
        if _trend_slope(values) <= threshold:
            contributing.append(signal_name)


def _trend_slope(values: Sequence[float]) -> float:
    """Least-squares slope of `values` against generation index — a
    simple, transparent linear trend, not a claim about the true
    underlying dynamics."""
    x = np.arange(len(values), dtype=np.float64)
    y = np.asarray(values, dtype=np.float64)
    slope, _intercept = np.polyfit(x, y, deg=1)
    return float(slope)
