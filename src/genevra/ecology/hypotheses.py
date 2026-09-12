"""Phase 15.11: ecology x evolvability as explicit, testable hypotheses —
never an assumed causal chain.

Mirrors `genevra.literature.claims.LiteratureClaim`'s structured-field
convention: every hypothesis names its null/alternative, independent/
dependent variable, required control, and statistical test up front, so
a result is checked against a pre-registered expectation rather than a
metric chosen after looking at the data.
"""

from __future__ import annotations

import dataclasses
from collections.abc import Sequence
from dataclasses import dataclass
from enum import StrEnum
from typing import Any

import numpy as np

from genevra.analysis.aggregation import bootstrap_confidence_interval, cohens_d, permutation_test


@dataclass(frozen=True)
class EcologyHypothesis:
    hypothesis_id: str
    null_hypothesis: str
    alternative_hypothesis: str
    independent_variable: str
    dependent_variable: str
    control: str
    statistical_test: str
    effect_size_measure: str
    uncertainty_measure: str
    replication_requirement: str

    def to_dict(self) -> dict[str, Any]:
        return dataclasses.asdict(self)


H1_COMPETITION_CHANGES_LEARNING_STRATEGY = EcologyHypothesis(
    hypothesis_id="H1_competition_changes_learning_strategy",
    null_hypothesis=(
        "Mean plasticity_gate does not differ between weak- and strong-competition conditions."
    ),
    alternative_hypothesis=(
        "Mean plasticity_gate differs between weak- and strong-competition conditions."
    ),
    independent_variable="competition strength (resource density / max_agents)",
    dependent_variable="mean plasticity_gate at the end of the run",
    control="same architecture, mutation operator, seed schedule; only competition strength varies",
    statistical_test="permutation test on the seed-level mean difference",
    effect_size_measure="Cohen's d",
    uncertainty_measure="bootstrap 90% CI on each condition's seed-level mean",
    replication_requirement=">= 3 independent seeds per condition",
)

H2_STRATEGY_PREDICTS_ADAPTATION = EcologyHypothesis(
    hypothesis_id="H2_strategy_predicts_adaptation",
    null_hypothesis="Learning-strategy composition does not predict lifetime adaptation gain.",
    alternative_hypothesis=(
        "Learning-strategy composition (mean plasticity_gate) is associated with "
        "lifetime adaptation gain."
    ),
    independent_variable="mean plasticity_gate",
    dependent_variable="adaptation gain (genevra.metrics.adaptation)",
    control="same environment config across compared genotypes",
    statistical_test="Pearson correlation, seed-level",
    effect_size_measure="correlation coefficient",
    uncertainty_measure="bootstrap 90% CI on the correlation coefficient",
    replication_requirement=">= 3 independent seeds",
)

H3_SPECIALIZATION_CHANGES_ROBUSTNESS = EcologyHypothesis(
    hypothesis_id="H3_specialization_changes_robustness",
    null_hypothesis=(
        "Ecological specialization does not differ in mutational robustness from generalists."
    ),
    alternative_hypothesis=(
        "Specialist and generalist genotypes (by NicheProfile.specialization) differ "
        "in mutational robustness."
    ),
    independent_variable="specialist vs generalist classification (genevra.ecology.roles)",
    dependent_variable="RobustnessProfile.genetic.mean (genevra.mechanisms.robustness)",
    control="same mutation operator and perturbation sampling for both groups",
    statistical_test="permutation test on the group mean difference",
    effect_size_measure="Cohen's d",
    uncertainty_measure="bootstrap 90% CI per group",
    replication_requirement=">= 3 genotypes per group, ideally from independent seeds",
)

H4_DIVERSITY_CHANGES_EVOLVABILITY = EcologyHypothesis(
    hypothesis_id="H4_diversity_changes_evolvability",
    null_hypothesis="Ecological (niche) diversity does not predict behavioral evolvability.",
    alternative_hypothesis=(
        "Higher niche diversity is associated with higher mean_behavioral_distance "
        "(EvolvabilityReport)."
    ),
    independent_variable="PopulationNicheSummary.mean_breadth",
    dependent_variable="EvolvabilityReport.mean_behavioral_distance",
    control="same mutation operator, sample size, environment across seeds",
    statistical_test="Pearson correlation, seed-level",
    effect_size_measure="correlation coefficient",
    uncertainty_measure="bootstrap 90% CI on the correlation coefficient",
    replication_requirement=">= 3 independent seeds",
)

H5_INTERACTION_PRESSURE_CHANGES_INNOVATION = EcologyHypothesis(
    hypothesis_id="H5_interaction_pressure_changes_innovation",
    null_hypothesis=(
        "Interaction pressure (competition-event rate) does not predict future innovation rate."
    ),
    alternative_hypothesis=(
        "Higher competition-event rate is associated with a higher subsequent "
        "innovation rate (genevra.innovation)."
    ),
    independent_variable="competition events per step (InteractionNetwork-derived rate)",
    dependent_variable="innovation event rate in a later generation window",
    control="same architecture/mutation operator; only competition intensity varies",
    statistical_test=(
        "permutation test on the seed-level rate difference between high/low competition conditions"
    ),
    effect_size_measure="Cohen's d",
    uncertainty_measure="bootstrap 90% CI per condition",
    replication_requirement=">= 3 independent seeds per condition",
)

ALL_ECOLOGY_HYPOTHESES: tuple[EcologyHypothesis, ...] = (
    H1_COMPETITION_CHANGES_LEARNING_STRATEGY,
    H2_STRATEGY_PREDICTS_ADAPTATION,
    H3_SPECIALIZATION_CHANGES_ROBUSTNESS,
    H4_DIVERSITY_CHANGES_EVOLVABILITY,
    H5_INTERACTION_PRESSURE_CHANGES_INNOVATION,
)


class AssociationLabel(StrEnum):
    ASSOCIATION_FOUND = "association_found"
    NO_ASSOCIATION_FOUND = "no_association_found"
    INSUFFICIENT_DATA = "insufficient_data"


@dataclass(frozen=True)
class EcologyHypothesisTestResult:
    hypothesis: EcologyHypothesis
    label: AssociationLabel
    observed_difference: float | None
    p_value: float | None
    effect_size: float | None
    confidence_interval: tuple[float, float] | None
    n_a: int
    n_b: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "hypothesis": self.hypothesis.to_dict(),
            "label": self.label.value,
            "observed_difference": self.observed_difference,
            "p_value": self.p_value,
            "effect_size": self.effect_size,
            "confidence_interval": self.confidence_interval,
            "n_a": self.n_a,
            "n_b": self.n_b,
        }


def test_ecology_hypothesis(
    hypothesis: EcologyHypothesis,
    sample_a: Sequence[float],
    sample_b: Sequence[float],
    rng: np.random.Generator,
    alpha: float = 0.05,
    min_seeds: int = 3,
) -> EcologyHypothesisTestResult:
    """Two-sample permutation test where each value in `sample_a`/
    `sample_b` is one independent seed's aggregate — never per-organism
    values (Phase 16.1/16.12's replication-unit requirement). Returns
    `INSUFFICIENT_DATA` rather than a p-value when either sample has
    fewer than `min_seeds` observations."""
    if len(sample_a) < min_seeds or len(sample_b) < min_seeds:
        return EcologyHypothesisTestResult(
            hypothesis,
            AssociationLabel.INSUFFICIENT_DATA,
            None,
            None,
            None,
            None,
            len(sample_a),
            len(sample_b),
        )
    perm = permutation_test(sample_a, sample_b, rng)
    effect = cohens_d(sample_a, sample_b)
    ci = bootstrap_confidence_interval(list(sample_a) + list(sample_b), rng)
    label = (
        AssociationLabel.ASSOCIATION_FOUND
        if perm.p_value < alpha
        else AssociationLabel.NO_ASSOCIATION_FOUND
    )
    return EcologyHypothesisTestResult(
        hypothesis=hypothesis,
        label=label,
        observed_difference=perm.observed_difference,
        p_value=perm.p_value,
        effect_size=effect.cohens_d,
        confidence_interval=(ci.low, ci.high),
        n_a=len(sample_a),
        n_b=len(sample_b),
    )


__all__ = [
    "EcologyHypothesis",
    "H1_COMPETITION_CHANGES_LEARNING_STRATEGY",
    "H2_STRATEGY_PREDICTS_ADAPTATION",
    "H3_SPECIALIZATION_CHANGES_ROBUSTNESS",
    "H4_DIVERSITY_CHANGES_EVOLVABILITY",
    "H5_INTERACTION_PRESSURE_CHANGES_INNOVATION",
    "ALL_ECOLOGY_HYPOTHESES",
    "AssociationLabel",
    "EcologyHypothesisTestResult",
    "test_ecology_hypothesis",
]
