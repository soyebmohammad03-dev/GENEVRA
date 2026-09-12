"""Phase 16.3: population-level evolvability, aggregating Phase 13/8's
per-genotype `EvolvabilityReport`s across seeds.

Each field is reported as a distribution across seeds (mean, std, and the
raw per-seed values), never collapsed to one number without the spread —
Phase 16.3's explicit requirement. `EvolvabilityReport` fields that are
themselves `None` for a given seed (e.g. no `fitness_evaluator` was
supplied, so `beneficial_fraction` is `None`) are excluded from that
field's distribution rather than treated as zero.
"""

from __future__ import annotations

import dataclasses
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any

import numpy as np

from genevra.metrics.evolvability import EvolvabilityReport


@dataclass(frozen=True)
class FieldDistribution:
    n: int
    mean: float | None
    std: float | None
    values: tuple[float, ...]

    def to_dict(self) -> dict[str, Any]:
        return dataclasses.asdict(self)


def _distribution(values: list[float | None]) -> FieldDistribution:
    present = [v for v in values if v is not None]
    if not present:
        return FieldDistribution(0, None, None, ())
    arr = np.asarray(present, dtype=np.float64)
    return FieldDistribution(len(present), float(arr.mean()), float(arr.std()), tuple(present))


@dataclass(frozen=True)
class PopulationEvolvabilityProfile:
    n_seeds: int
    mean_behavioral_distance: FieldDistribution
    viable_fraction: FieldDistribution
    beneficial_fraction: FieldDistribution
    neutral_fraction: FieldDistribution
    deleterious_fraction: FieldDistribution

    def to_dict(self) -> dict[str, Any]:
        return {
            "n_seeds": self.n_seeds,
            "mean_behavioral_distance": self.mean_behavioral_distance.to_dict(),
            "viable_fraction": self.viable_fraction.to_dict(),
            "beneficial_fraction": self.beneficial_fraction.to_dict(),
            "neutral_fraction": self.neutral_fraction.to_dict(),
            "deleterious_fraction": self.deleterious_fraction.to_dict(),
        }


class PopulationEvolvabilityAnalyzer:
    """Aggregates one `EvolvabilityReport` per seed (typically computed
    by `genevra.metrics.evolvability.EvolvabilityAnalyzer` against a
    representative genome from that seed's population) into
    across-seed distributions."""

    def summarize(self, reports: Sequence[EvolvabilityReport]) -> PopulationEvolvabilityProfile:
        return PopulationEvolvabilityProfile(
            n_seeds=len(reports),
            mean_behavioral_distance=_distribution([r.mean_behavioral_distance for r in reports]),
            viable_fraction=_distribution([r.viable_fraction for r in reports]),
            beneficial_fraction=_distribution([r.beneficial_fraction for r in reports]),
            neutral_fraction=_distribution([r.neutral_fraction for r in reports]),
            deleterious_fraction=_distribution([r.deleterious_fraction for r in reports]),
        )


__all__ = [
    "FieldDistribution",
    "PopulationEvolvabilityProfile",
    "PopulationEvolvabilityAnalyzer",
]
