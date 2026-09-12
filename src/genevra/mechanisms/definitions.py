"""Phase 13.1: a formal, structured definition record for every trait
this package measures.

Every analyzer in `genevra.mechanisms` attaches a `MetricDefinition` to
its report rather than relying on a docstring or a field name like
"adaptability_score" to carry the meaning. `is_realized` distinguishes
what a population/genotype actually produced (a `False` value here means
"potential": what it *could* produce under controlled perturbation) —
this is Phase 13.6/12.6's realized-vs-potential distinction, made
explicit per metric instead of left implicit.
"""

from __future__ import annotations

import dataclasses
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class MetricDefinition:
    name: str
    definition: str
    input_data: str
    math_definition: str
    interpretation: str
    limitations: str
    is_realized: bool
    """True: measures what actually happened (a realized outcome). False:
    measures what controlled perturbation/sampling could produce (a
    potential), not a guarantee it will be realized under selection."""
    provenance_version: str

    def to_dict(self) -> dict[str, Any]:
        return dataclasses.asdict(self)


ROBUSTNESS_DEFINITION = MetricDefinition(
    name="robustness",
    definition=(
        "Preservation of phenotype, behavior, fitness, or lifetime-learned behavior "
        "under a controlled perturbation (one-step mutation, repeated stochastic "
        "re-evaluation, or an environment-parameter shift)."
    ),
    input_data=(
        "One genome; a mutation operator, environment config(s), organism config, and "
        "learning rule sufficient to run repeated lifetimes."
    ),
    math_definition=(
        "For a set of N perturbed evaluations, the distribution (mean, std, 10th "
        "percentile) of a distance/delta from the unperturbed baseline: behavioral "
        "signature distance for genetic/behavioral/learning robustness, |fitness "
        "delta| for fitness/environmental robustness. Lower values indicate higher "
        "robustness; this module reports the raw distribution, never inverts it into "
        "a single 'robustness score.'"
    ),
    interpretation=(
        "A tight (low-mean, low-std) distribution means this genotype's evaluated "
        "outcome is stable under the tested perturbation kind. It is not a claim "
        "about robustness under perturbation kinds not tested here."
    ),
    limitations=(
        "Sampled, not exhaustive (bounded num_samples for laptop feasibility). "
        "Single-genotype, on-demand measurement, not a per-generation population "
        "statistic. Robustness is not the inverse of fitness — a robust genotype "
        "can have low fitness."
    ),
    is_realized=False,
    provenance_version="mechanisms.robustness.v1",
)

PLASTICITY_COST_DEFINITION = MetricDefinition(
    name="plasticity_cost",
    definition=(
        "Association between an evolved population's plasticity_gate (heritable "
        "control of how much lifetime-learned change is expressed; see "
        "genevra.organism.learning.LearningParams) and other measured traits, "
        "reported as benefit-vs-cost evidence rather than an assumed net benefit."
    ),
    input_data=(
        "Sampled genomes from a population (or a stored ExperimentResult's final "
        "generation), each yielding a LearningStrategy, an initial_competence value, "
        "and (optionally) an EvolvabilityReport/RobustnessProfile."
    ),
    math_definition=(
        "Pearson correlation between plasticity_gate and each of: initial_competence "
        "(pre-learning baseline performance), genetic robustness, and evolvability "
        "viable_fraction/mean_behavioral_distance, computed only when >= 3 non-missing "
        "paired observations exist (genevra.analysis.tradeoff's convention)."
    ),
    interpretation=(
        "A negative correlation with initial_competence is consistent with a "
        "'plasticity trades off against baseline competence' cost; this module makes "
        "no claim of causation from a correlational finding."
    ),
    limitations=(
        "GENEVRA's metabolism model (genevra.organism.metabolism) does not currently "
        "attach a metabolic energy cost to a nonzero plasticity_gate or learning_rate "
        "— that mechanism does not exist in the organism model, so no metabolic-cost "
        "measurement is fabricated here. Only costs measurable from existing model "
        "quantities (competence, robustness, evolvability) are reported. Computational "
        "cost of the Hebbian update itself is negligible at GENEVRA's scale and is not "
        "measured."
    ),
    is_realized=True,
    provenance_version="mechanisms.plasticity_cost.v1",
)

GENERALIZATION_DEFINITION = MetricDefinition(
    name="generalization",
    definition=(
        "Fitness, adaptation speed, and behavioral change when the same genome is "
        "evaluated in environments other than the one it evolved in."
    ),
    input_data=(
        "One genome; a labeled set of GridWorldConfig variants (train / recurrent: "
        "same config, new seed / related_unseen: one parameter shifted moderately / "
        "novel: parameters shifted substantially)."
    ),
    math_definition=(
        "Per environment: fitness (FitnessFunction.compute), AdaptationCurve "
        "(initial/final competence via genevra.metrics.adaptation), and behavioral "
        "signature distance from the train-environment baseline signature."
    ),
    interpretation=(
        "Retention is fitness_in_environment / fitness_in_train (>1 means it "
        "performed better in that environment than its own training one). This "
        "profile reports where performance held up; it does not attribute *why* "
        "(genetic, lifetime-learned, or behavioral generalization) without a "
        "separate learning-rule-ablated comparison."
    ),
    limitations=(
        "'Novel' environments here are parameter shifts within the same GridWorld "
        "model (density/size), not qualitatively new dynamics — this is a bounded, "
        "operational notion of novelty, not a claim of unbounded generalization."
    ),
    is_realized=True,
    provenance_version="mechanisms.generalization.v1",
)

EVOLVABILITY_PROFILE_DEFINITION = MetricDefinition(
    name="evolvability_profile",
    definition=(
        "A multidimensional composition of existing evolvability measurements "
        "(genevra.metrics.evolvability) plus generalization-potential and "
        "strategy-space components, kept as a vector rather than collapsed into "
        "one score."
    ),
    input_data="One or more EvolvabilityReport/GeneralizationProfile results for a genome.",
    math_definition=(
        "A frozen dataclass of independently-computed fields: "
        "mutational_phenotypic_variance, beneficial_fraction, novel_environment_fitness, "
        "recurrent_environment_fitness, adaptation_gain. No default aggregate weighting "
        "is applied; a caller-supplied weight mapping is required to produce a scalar."
    ),
    interpretation=(
        "Each field answers a different question about evolutionary potential; a high "
        "value on one field does not imply a high value on another."
    ),
    limitations=(
        "All fields are potential (mutation/environment-perturbation) measurements at "
        "one point in time, not observed evolutionary outcomes."
    ),
    is_realized=False,
    provenance_version="mechanisms.evolvability_profile.v1",
)

__all__ = [
    "MetricDefinition",
    "ROBUSTNESS_DEFINITION",
    "PLASTICITY_COST_DEFINITION",
    "GENERALIZATION_DEFINITION",
    "EVOLVABILITY_PROFILE_DEFINITION",
]
