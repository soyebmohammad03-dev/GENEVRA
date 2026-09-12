"""Phase 15.10: ecological regime transitions.

Reuses `genevra.analysis.regime_detection.detect_change_points` (the
existing permutation-tested change-point detector) rather than a second
detection mechanism; this module only adds post-hoc, data-driven labels
for what kind of ecological transition a detected change point in a
given metric is *consistent with*. A label here is a candidate
description, never a causal claim — the same caveat
`regime_detection.ChangePoint` already carries.
"""

from __future__ import annotations

import dataclasses
from dataclasses import dataclass
from typing import Any

import numpy as np

from genevra.analysis.regime_detection import ChangePoint, ChangePointConfig, detect_change_points

_LABEL_RULES: dict[str, tuple[str, str]] = {
    "diversity": ("diversity_collapse", "coexistence_emergence"),
    "evenness": ("specialization_burst", "coexistence_emergence"),
    "concentration_hhi": ("coexistence_emergence", "competitive_exclusion"),
    "niche_overlap": ("niche_separation", "niche_convergence"),
    "interaction_type_diversity": ("network_restructuring", "network_restructuring"),
    "population_size": ("diversity_collapse", "recovery"),
}
"""metric_name -> (label if the metric *decreased*, label if it
*increased*) at a detected change point. Data-driven in the sense that
*where* a transition is flagged comes entirely from
`detect_change_points`'s permutation test; only *which name* to attach
to a decrease vs. an increase is a fixed, documented mapping — not a
magic numeric threshold."""


@dataclass(frozen=True)
class EcologicalRegimeTransition:
    change_point: ChangePoint
    candidate_label: str
    confidence: str
    """Always `"candidate"` — this module never asserts `"confirmed"`;
    see module docstring."""

    def to_dict(self) -> dict[str, Any]:
        return {
            "change_point": dataclasses.asdict(self.change_point),
            "candidate_label": self.candidate_label,
            "confidence": self.confidence,
        }


def detect_ecological_regime_transitions(
    metric_name: str,
    values: list[float],
    rng: np.random.Generator,
    generations: list[int] | None = None,
    config: ChangePointConfig | None = None,
) -> list[EcologicalRegimeTransition]:
    change_points = detect_change_points(values, metric_name, rng, generations, config)
    decrease_label, increase_label = _LABEL_RULES.get(
        metric_name, ("unlabeled_transition", "unlabeled_transition")
    )
    transitions = []
    for cp in change_points:
        label = decrease_label if cp.after_mean < cp.before_mean else increase_label
        transitions.append(EcologicalRegimeTransition(cp, label, confidence="candidate"))
    return transitions


__all__ = ["EcologicalRegimeTransition", "detect_ecological_regime_transitions"]
