"""Phase 11.5: structured competing explanations for an observed
association.

`standard_alternative_explanations` never decides which explanation is
correct — it only names, for each of the ten confounds Phase 11.5 lists,
the signature that would distinguish it and the control a discriminating
experiment would need. `status` starts `"untested"` for every generated
entry; only actually running the named discriminating experiment (see
`genevra.literature.falsification`) and recording its outcome should ever
move it to `"ruled_out"` / `"supported"` / `"inconclusive"`.
"""

from __future__ import annotations

import dataclasses
from dataclasses import dataclass
from typing import Any, Literal

ExplanationStatus = Literal["untested", "ruled_out", "supported", "inconclusive"]

STANDARD_CONFOUNDS: tuple[str, ...] = (
    "mutation_rate",
    "population_size",
    "environmental_volatility",
    "environmental_predictability",
    "cue_reliability",
    "lineage_history",
    "survival_bias",
    "baseline_fitness",
    "metric_definition",
    "stochastic_variation",
)


@dataclass(frozen=True)
class AlternativeExplanation:
    explanation_id: str
    description: str
    predicted_signature: str
    discriminating_experiment: str
    required_control: str
    status: ExplanationStatus = "untested"
    evidence: tuple[str, ...] = ()
    provenance: tuple[str, ...] = ()
    """`ResearchMemory` record ids of whatever evidence updated `status`
    away from `"untested"` — empty until a discriminating experiment has
    actually run."""

    def to_dict(self) -> dict[str, Any]:
        return dataclasses.asdict(self)


def standard_alternative_explanations(
    independent_variable: str, dependent_variable: str
) -> list[AlternativeExplanation]:
    """One templated `AlternativeExplanation` per confound in
    `STANDARD_CONFOUNDS`, for the observed
    `independent_variable -> dependent_variable` association."""
    explanations = []
    for confound in STANDARD_CONFOUNDS:
        label = confound.replace("_", " ")
        explanations.append(
            AlternativeExplanation(
                explanation_id=f"{independent_variable}::{dependent_variable}::{confound}",
                description=(
                    f"{label} may drive the observed association between "
                    f"{independent_variable} and {dependent_variable}, rather than "
                    f"{independent_variable} itself."
                ),
                predicted_signature=(
                    f"controlling for {label} attenuates or removes the "
                    f"{independent_variable}-{dependent_variable} association"
                ),
                discriminating_experiment=(
                    f"hold {label} fixed across conditions while varying "
                    f"{independent_variable} (or vice versa), then re-run the comparison"
                ),
                required_control=f"a condition matched on {label}",
            )
        )
    return explanations


__all__ = [
    "ExplanationStatus",
    "STANDARD_CONFOUNDS",
    "AlternativeExplanation",
    "standard_alternative_explanations",
]
