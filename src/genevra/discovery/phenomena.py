"""Phase 10.1: a modular `PhenomenonDetector` framework for scanning
experiment trajectories for scientifically interesting patterns.

`PhenomenonRule` implementations below (novelty/fitness decoupling,
diversity collapse while novelty continues) are *examples*, not an
exhaustive or hardcoded list of "the discoveries GENEVRA can make" — new
rules are added by implementing the `PhenomenonRule` protocol, not by
editing `PhenomenonDetector`.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any, Protocol

from genevra.analysis.stagnation import _trend_slope


@dataclass(frozen=True)
class PhenomenonObservation:
    """A candidate pattern found in one experiment/seed's trajectory —
    not a claim it generalizes, and not a claim it is causally
    meaningful. `evidence` carries the raw numbers a researcher would
    need to check the claim by hand."""

    name: str
    description: str
    experiment: str
    seed: int
    evidence: dict[str, Any]
    generation_range: tuple[int, int] | None = None
    note: str = field(
        default="A candidate pattern under this rule's definition and this run's "
        "data only. Not evidence of a general effect until checked across seeds/conditions."
    )


class PhenomenonRule(Protocol):
    name: str

    def detect(
        self, trajectory: Sequence[Mapping[str, Any]], experiment: str, seed: int
    ) -> list[PhenomenonObservation]: ...


def _series(trajectory: Sequence[Mapping[str, Any]], key: str) -> list[float]:
    return [float(g[key]) for g in trajectory]


class NoveltyWithoutFitnessGainRule:
    """ "Novelty increases while fitness remains flat" (one of Phase
    10.1's example phenomena): novelty trend slope is clearly positive
    while the fitness trend slope is within `fitness_flat_threshold` of
    zero."""

    name = "novelty_without_fitness_gain"

    def __init__(
        self, novelty_slope_threshold: float = 0.001, fitness_flat_threshold: float = 0.05
    ) -> None:
        self._novelty_slope_threshold = novelty_slope_threshold
        self._fitness_flat_threshold = fitness_flat_threshold

    def detect(
        self, trajectory: Sequence[Mapping[str, Any]], experiment: str, seed: int
    ) -> list[PhenomenonObservation]:
        if len(trajectory) < 3:
            return []
        novelty = _series(trajectory, "instantaneous_novelty")
        fitness = [float(g["fitness_summary"]["mean"]) for g in trajectory]
        novelty_slope = _trend_slope(novelty)
        fitness_slope = _trend_slope(fitness)
        if novelty_slope > self._novelty_slope_threshold and (
            abs(fitness_slope) < self._fitness_flat_threshold
        ):
            return [
                PhenomenonObservation(
                    name=self.name,
                    description="Behavioral novelty increased while mean fitness stayed flat.",
                    experiment=experiment,
                    seed=seed,
                    evidence={"novelty_slope": novelty_slope, "fitness_slope": fitness_slope},
                    generation_range=(
                        int(trajectory[0]["generation"]),
                        int(trajectory[-1]["generation"]),
                    ),
                )
            ]
        return []


class DiversityCollapseWithContinuedNoveltyRule:
    """ "Diversity collapses while novelty continues" — genotypic diversity
    trend is clearly negative while novelty trend is non-negative."""

    name = "diversity_collapse_with_continued_novelty"

    def __init__(
        self, diversity_slope_threshold: float = -0.001, novelty_flat_threshold: float = 0.0
    ) -> None:
        self._diversity_slope_threshold = diversity_slope_threshold
        self._novelty_flat_threshold = novelty_flat_threshold

    def detect(
        self, trajectory: Sequence[Mapping[str, Any]], experiment: str, seed: int
    ) -> list[PhenomenonObservation]:
        if len(trajectory) < 3:
            return []
        diversity = _series(trajectory, "genotypic_diversity")
        novelty = _series(trajectory, "instantaneous_novelty")
        diversity_slope = _trend_slope(diversity)
        novelty_slope = _trend_slope(novelty)
        if (
            diversity_slope < self._diversity_slope_threshold
            and novelty_slope >= self._novelty_flat_threshold
        ):
            return [
                PhenomenonObservation(
                    name=self.name,
                    description=(
                        "Genotypic diversity declined while behavioral novelty did not, "
                        "suggesting continued behavioral variation from a narrowing gene pool."
                    ),
                    experiment=experiment,
                    seed=seed,
                    evidence={"diversity_slope": diversity_slope, "novelty_slope": novelty_slope},
                    generation_range=(
                        int(trajectory[0]["generation"]),
                        int(trajectory[-1]["generation"]),
                    ),
                )
            ]
        return []


class RepeatedRegimeRule:
    """ "Evolution repeatedly enters similar regimes": the fitness
    trajectory's trend slope changes sign at least `min_sign_changes`
    times over the run — a crude proxy for oscillation between regimes
    rather than a single monotonic trajectory."""

    name = "repeated_regime_oscillation"

    def __init__(self, window: int = 5, min_sign_changes: int = 2) -> None:
        if window < 2:
            raise ValueError("window must be >= 2")
        self._window = window
        self._min_sign_changes = min_sign_changes

    def detect(
        self, trajectory: Sequence[Mapping[str, Any]], experiment: str, seed: int
    ) -> list[PhenomenonObservation]:
        fitness = [float(g["fitness_summary"]["mean"]) for g in trajectory]
        if len(fitness) < self._window * 2:
            return []
        slopes = [
            _trend_slope(fitness[i : i + self._window])
            for i in range(0, len(fitness) - self._window + 1, self._window)
        ]
        signs = [1 if s > 0 else (-1 if s < 0 else 0) for s in slopes if s != 0]
        sign_changes = sum(1 for a, b in zip(signs, signs[1:], strict=False) if a != b)
        if sign_changes >= self._min_sign_changes:
            return [
                PhenomenonObservation(
                    name=self.name,
                    description="Fitness trend direction reversed repeatedly across the run.",
                    experiment=experiment,
                    seed=seed,
                    evidence={"window_slopes": slopes, "sign_changes": sign_changes},
                    generation_range=(
                        int(trajectory[0]["generation"]),
                        int(trajectory[-1]["generation"]),
                    ),
                )
            ]
        return []


DEFAULT_RULES: tuple[PhenomenonRule, ...] = (
    NoveltyWithoutFitnessGainRule(),
    DiversityCollapseWithContinuedNoveltyRule(),
    RepeatedRegimeRule(),
)


class PhenomenonDetector:
    def __init__(self, rules: Sequence[PhenomenonRule] = DEFAULT_RULES) -> None:
        if not rules:
            raise ValueError("at least one rule is required")
        self._rules = rules

    def detect(
        self, trajectory: Sequence[Mapping[str, Any]], experiment: str, seed: int
    ) -> list[PhenomenonObservation]:
        return [
            observation
            for rule in self._rules
            for observation in rule.detect(trajectory, experiment, seed)
        ]


__all__ = [
    "PhenomenonObservation",
    "PhenomenonRule",
    "PhenomenonDetector",
    "NoveltyWithoutFitnessGainRule",
    "DiversityCollapseWithContinuedNoveltyRule",
    "RepeatedRegimeRule",
    "DEFAULT_RULES",
]
