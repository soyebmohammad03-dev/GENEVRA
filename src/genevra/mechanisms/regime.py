"""Phase 13.10: an evolutionary-regime label per generation, built from
data-driven thresholds (each metric's own trajectory quantiles) rather
than magic-number constants, reusing `StagnationAnalyzer` (already the
project's stagnation/plateau detector — not reimplemented here) and
`detect_change_points` (already the project's change-point detector).

Labels are descriptive summaries of measured trend/threshold conditions
at one generation, never a claim about the underlying evolutionary
process — the same caution `regime_detection.py`'s module docstring
states for change points.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

import numpy as np

from genevra.analysis.regime_detection import ChangePoint
from genevra.analysis.stagnation import StagnationAnalyzer, StagnationConfig

_REGIME_LABELS: tuple[str, ...] = (
    "exploration",
    "exploitation",
    "innovation_burst",
    "adaptation",
    "stabilization",
    "stagnation",
    "recovery",
    "strategy_transition",
    "environmental_response",
)


@dataclass(frozen=True)
class RegimeClassification:
    generation: int
    labels: tuple[str, ...]
    """One generation may match more than one label; an empty tuple is a
    valid, honest result (no configured criterion was met)."""
    evidence: dict[str, float]
    note: str = (
        "Each label reflects a quantile-based threshold on that generation's own "
        "trailing-window trend or a coincident change point, not a hand-picked "
        "constant. Multiple labels may co-occur; this is a descriptive summary, not "
        "a hidden Markov model or any claim of mutually exclusive process states."
    )


@dataclass(frozen=True)
class RegimeClassifierConfig:
    window: int = 5
    high_quantile: float = 0.75
    low_quantile: float = 0.25
    stagnation_config: StagnationConfig | None = None


def classify_regimes(
    trajectory: Sequence[Mapping[str, Any]],
    change_points: Sequence[ChangePoint],
    config: RegimeClassifierConfig | None = None,
) -> list[RegimeClassification]:
    """`trajectory` is `Trajectory.to_dict()`-shaped. `change_points` is
    typically the pooled output of
    `genevra.analysis.regime_detection.detect_regime_transitions` across
    whichever metrics were tracked for this run."""
    cfg = config if config is not None else RegimeClassifierConfig()
    stagnation_analyzer = StagnationAnalyzer(cfg.stagnation_config or StagnationConfig())

    diversity_series = np.array([float(g["genotypic_diversity"]) for g in trajectory])
    novelty_series = np.array([float(g["instantaneous_novelty"]) for g in trajectory])
    fitness_series = np.array([float(g["fitness_summary"]["mean"]) for g in trajectory])

    high_diversity = (
        float(np.quantile(diversity_series, cfg.high_quantile)) if len(diversity_series) else 0.0
    )
    low_diversity = (
        float(np.quantile(diversity_series, cfg.low_quantile)) if len(diversity_series) else 0.0
    )
    high_novelty = (
        float(np.quantile(novelty_series, cfg.high_quantile)) if len(novelty_series) else 0.0
    )
    change_by_generation: dict[int, list[ChangePoint]] = {}
    for cp in change_points:
        change_by_generation.setdefault(cp.generation, []).append(cp)

    results: list[RegimeClassification] = []
    for i, gen_snapshot in enumerate(trajectory):
        generation = int(gen_snapshot["generation"])
        labels: list[str] = []
        evidence: dict[str, float] = {}

        window = trajectory[max(0, i - cfg.window + 1) : i + 1]
        stagnation_report = stagnation_analyzer.analyze(window)
        evidence["stagnation_score"] = stagnation_report.stagnation_score
        stagnation_threshold = (
            cfg.stagnation_config.min_signal_fraction_to_detect if cfg.stagnation_config else 0.5
        )
        if stagnation_report.stagnation_score >= stagnation_threshold:
            labels.append("stagnation")

        if diversity_series[i] >= high_diversity:
            labels.append("exploration")
        elif diversity_series[i] <= low_diversity:
            labels.append("exploitation")

        if novelty_series[i] >= high_novelty:
            labels.append("innovation_burst")

        if i > 0 and fitness_series[i] > fitness_series[i - 1] and "stagnation" not in labels:
            labels.append("adaptation")

        cps_here = change_by_generation.get(generation, [])
        for cp in cps_here:
            if cp.metric_name == "learning_strategy_diversity":
                labels.append("strategy_transition")
            elif cp.magnitude < 0 and "stagnation" in labels:
                labels.append("recovery")
            elif cp.metric_name in ("genotypic_diversity", "behavioral_diversity"):
                labels.append("environmental_response")
        if (
            cps_here
            and "stagnation" not in labels
            and not any(
                lbl in labels for lbl in ("exploration", "exploitation", "innovation_burst")
            )
        ):
            labels.append("stabilization")

        results.append(
            RegimeClassification(
                generation=generation, labels=tuple(dict.fromkeys(labels)), evidence=evidence
            )
        )
    return results


__all__ = ["RegimeClassification", "RegimeClassifierConfig", "classify_regimes", "_REGIME_LABELS"]
