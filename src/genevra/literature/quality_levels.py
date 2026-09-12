"""Phase 18.3: reproduction quality levels — never conflate a directional
match at one parameter value with a "full replication."

LEVEL_0 (conceptual correspondence) is automatically true for any case in
`genevra.literature.cases`: mapping an independent/dependent variable pair
onto GENEVRA constructs is the case's entire reason for existing.
LEVEL_1/2 come straight from `ReproductionLabel`/`EffectSizeResult`.
LEVEL_3 (mechanistic reproduction) is deliberately NEVER auto-assigned
here — GENEVRA has no code path that verifies a claimed *mechanism*
(as opposed to a directional/quantitative pattern) reproduces; assigning
it would require an explicit mechanistic study this module does not
perform, so `classify_quality_level` caps out at LEVEL_2 unless the
caller explicitly supplies `mechanistic_evidence=True` from such a study.
LEVEL_4 requires >=2 tested regimes (a real boundary-condition sweep, not
one point) all landing at LEVEL_2, plus the spec's own multi-seed
replication requirement being met.
"""

from __future__ import annotations

from enum import IntEnum

from genevra.literature.runner import ReproductionLabel, ReproductionResult
from genevra.literature.spec import LiteratureExperimentSpec


class ReproductionQualityLevel(IntEnum):
    LEVEL_0_CONCEPTUAL = 0
    LEVEL_1_QUALITATIVE = 1
    LEVEL_2_QUANTITATIVE = 2
    LEVEL_3_MECHANISTIC = 3
    LEVEL_4_ROBUST = 4


_DIRECTIONAL_LABELS = (
    ReproductionLabel.SUPPORTED,
    ReproductionLabel.PARTIALLY_SUPPORTED,
    ReproductionLabel.NOT_SUPPORTED,
    ReproductionLabel.CONTRADICTED,
)


def classify_single_result(
    result: ReproductionResult, mechanistic_evidence: bool = False
) -> ReproductionQualityLevel:
    """The quality level a *single* reproduction result can support on
    its own — LEVEL_4 (robust across regimes/seeds) cannot be determined
    from one result and is never returned here; use
    `classify_quality_level_across_regimes` for that."""
    if result.label not in _DIRECTIONAL_LABELS:
        return ReproductionQualityLevel.LEVEL_0_CONCEPTUAL
    if result.label in (ReproductionLabel.NOT_SUPPORTED, ReproductionLabel.CONTRADICTED):
        return ReproductionQualityLevel.LEVEL_1_QUALITATIVE
    # SUPPORTED or PARTIALLY_SUPPORTED: a real quantitative effect size exists.
    level = ReproductionQualityLevel.LEVEL_2_QUANTITATIVE
    if mechanistic_evidence:
        level = ReproductionQualityLevel.LEVEL_3_MECHANISTIC
    return level


def classify_quality_level_across_regimes(
    results_by_regime: dict[str, ReproductionResult],
    spec: LiteratureExperimentSpec,
) -> ReproductionQualityLevel:
    """LEVEL_4 requires: >= 2 distinct regimes tested, every one of them
    independently reaching LEVEL_2 (SUPPORTED/PARTIALLY_SUPPORTED), and
    at least `spec.replication_required_seeds` completed seeds in each —
    i.e. an actually-swept, actually-replicated finding, not one lucky
    parameter value."""
    if len(results_by_regime) < 2:
        return max(
            (classify_single_result(r) for r in results_by_regime.values()),
            default=ReproductionQualityLevel.LEVEL_0_CONCEPTUAL,
        )
    per_regime_levels = [classify_single_result(r) for r in results_by_regime.values()]
    all_quantitative = all(
        level >= ReproductionQualityLevel.LEVEL_2_QUANTITATIVE for level in per_regime_levels
    )
    all_replicated = all(
        r.n_control >= spec.replication_required_seeds
        and r.n_treatment >= spec.replication_required_seeds
        for r in results_by_regime.values()
    )
    if all_quantitative and all_replicated:
        return ReproductionQualityLevel.LEVEL_4_ROBUST
    return max(per_regime_levels)


__all__ = [
    "ReproductionQualityLevel",
    "classify_single_result",
    "classify_quality_level_across_regimes",
]
