"""Phase 19.6: conclusion-robustness classification.

Criteria are deliberately simple and stated up front rather than
invented after seeing a result: given a set of tested variants of one
finding (different seeds, parameter values, or analysis windows), each
labeled with the *sign* of the effect it produced, classify how
consistent that sign was.

    n_variants < 3                   -> INSUFFICIENT_DATA (no meaningful
                                         sensitivity claim with fewer
                                         than 3 independently tested
                                         variants)
    sign_agreement_fraction == 0.5   -> UNSTABLE (a genuine tie: no
                                         majority sign at all)
    sign_agreement_fraction >= 0.9   -> ROBUST
    sign_agreement_fraction >= 0.7   -> MODERATELY_ROBUST
    0.5 <  sign_agreement_fraction < 0.7 -> SENSITIVE

`sign_agreement_fraction` is the fraction of variants agreeing with the
majority sign, reusing
`genevra.population_analysis.replication_consistency`'s
`agreement_fraction` convention directly. Because that convention always
picks *some* majority sign, its agreement fraction is mathematically
bounded to `[0.5, 1.0]` for any nonzero-effect set — a fraction below
0.5 is not a value this computation can ever produce, so `UNSTABLE` is
defined at the one genuinely un-majority-having point (an exact 50/50
split) rather than an unreachable "< 0.5" branch.
"""

from __future__ import annotations

import dataclasses
from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from genevra.population_analysis.replication_consistency import summarize_replication_consistency


class RobustnessClassification(StrEnum):
    ROBUST = "ROBUST"
    MODERATELY_ROBUST = "MODERATELY_ROBUST"
    SENSITIVE = "SENSITIVE"
    UNSTABLE = "UNSTABLE"
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"


@dataclass(frozen=True)
class RobustnessSensitivityReport:
    finding_id: str
    tested_variants: dict[str, float]
    """`{variant_label: signed_effect_value}`, e.g.
    `{"seed_set_a": 0.31, "population_size_12": -0.02, ...}`."""
    agreement_fraction: float | None
    classification: RobustnessClassification
    reasons: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return dataclasses.asdict(self)


def classify_robustness(
    finding_id: str, tested_variants: Mapping[str, float]
) -> RobustnessSensitivityReport:
    if len(tested_variants) < 3:
        return RobustnessSensitivityReport(
            finding_id=finding_id,
            tested_variants=dict(tested_variants),
            agreement_fraction=None,
            classification=RobustnessClassification.INSUFFICIENT_DATA,
            reasons=(
                f"only {len(tested_variants)} variant(s) tested; at least 3 are required "
                "to say anything about sensitivity.",
            ),
        )
    # Reuse the existing sign-agreement machinery by treating each tested
    # variant as if it were one "seed" reporting one signed effect.
    consistency = summarize_replication_consistency(
        {i: v for i, v in enumerate(tested_variants.values())}
    )
    agreement = consistency.agreement_fraction
    if agreement is None:
        classification = RobustnessClassification.INSUFFICIENT_DATA
        reasons = ("every tested variant produced a zero effect; no sign to compare.",)
    elif agreement == 0.5:
        classification = RobustnessClassification.UNSTABLE
        reasons = ("tested variants split exactly evenly in sign; no majority direction.",)
    elif agreement >= 0.9:
        classification = RobustnessClassification.ROBUST
        reasons = (f"{agreement:.0%} of tested variants agree in sign.",)
    elif agreement >= 0.7:
        classification = RobustnessClassification.MODERATELY_ROBUST
        reasons = (f"{agreement:.0%} of tested variants agree in sign.",)
    else:
        classification = RobustnessClassification.SENSITIVE
        reasons = (f"only {agreement:.0%} of tested variants agree in sign.",)
    return RobustnessSensitivityReport(
        finding_id=finding_id,
        tested_variants=dict(tested_variants),
        agreement_fraction=agreement,
        classification=classification,
        reasons=reasons,
    )


__all__ = ["RobustnessClassification", "RobustnessSensitivityReport", "classify_robustness"]
