"""Phase 13.4: plasticity cost/benefit, not "plasticity is good."

GENEVRA's `Metabolism` (genevra.organism.metabolism) attaches no energy
cost to a nonzero `plasticity_gate` or `learning_rate` — those genes only
affect `HebbianLearning.effective_weights`, never `Metabolism.cost_for`.
Inventing a metabolic cost here would not be measuring GENEVRA, it would
be adding a new mechanism dressed up as an analysis. Instead this module
measures costs the existing model can actually produce evidence for:
association between an evolved population's `plasticity_gate` and other
already-computed traits, following
`genevra.analysis.tradeoff.summarize_tradeoff`'s convention (Pearson
correlation, >= 3 paired non-missing observations, `None` otherwise).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np

from genevra.mechanisms.definitions import PLASTICITY_COST_DEFINITION, MetricDefinition


@dataclass(frozen=True)
class PlasticityCostSample:
    """One sampled genotype's plasticity gate alongside whichever
    associated measurements were computed for it. Any field may be
    `None` when not measured for this sample — never defaulted, per
    `TradeoffSample`'s convention."""

    individual_id: int
    plasticity_gate: float
    initial_competence: float | None = None
    genetic_robustness_mean: float | None = None
    evolvability_viable_fraction: float | None = None
    evolvability_mean_behavioral_distance: float | None = None


@dataclass(frozen=True)
class PlasticityCostReport:
    associations: dict[str, float | None]
    n_samples: int
    definition: MetricDefinition = field(default=PLASTICITY_COST_DEFINITION)

    def to_dict(self) -> dict[str, Any]:
        return {
            "associations": self.associations,
            "n_samples": self.n_samples,
            "definition": self.definition.to_dict(),
        }


def _correlate(a: list[float | None], b: list[float | None]) -> float | None:
    pairs = [(x, y) for x, y in zip(a, b, strict=True) if x is not None and y is not None]
    if len(pairs) < 3:
        return None
    xs, ys = zip(*pairs, strict=True)
    if np.std(xs) == 0.0 or np.std(ys) == 0.0:
        return None
    return float(np.corrcoef(xs, ys)[0, 1])


def analyze_plasticity_cost(samples: list[PlasticityCostSample]) -> PlasticityCostReport:
    gates: list[float | None] = [s.plasticity_gate for s in samples]
    associations = {
        "plasticity_gate__vs__initial_competence": _correlate(
            gates, [s.initial_competence for s in samples]
        ),
        "plasticity_gate__vs__genetic_robustness": _correlate(
            gates, [s.genetic_robustness_mean for s in samples]
        ),
        "plasticity_gate__vs__evolvability_viable_fraction": _correlate(
            gates, [s.evolvability_viable_fraction for s in samples]
        ),
        "plasticity_gate__vs__evolvability_mean_behavioral_distance": _correlate(
            gates, [s.evolvability_mean_behavioral_distance for s in samples]
        ),
    }
    return PlasticityCostReport(associations=associations, n_samples=len(samples))


__all__ = ["PlasticityCostSample", "PlasticityCostReport", "analyze_plasticity_cost"]
