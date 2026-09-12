"""Phase 19.8: a unified metric registry for the evidence package.

Wraps `genevra.mechanisms.definitions.MetricDefinition` (Phase 13's
definition/math/interpretation/limitations record — reused, not
duplicated) with the three fields that record needs to serve as this
phase's registry entry: a stable `metric_id`, `units`, and the
`aggregation_level`/`replication_level` at which the metric in
`research_evidence/` was actually computed. Metrics that never got a
`MetricDefinition` in Phase 13 (fitness, diversity, novelty — plain
functions in `genevra.metrics`) get a minimal inline definition here
instead of a second full write-up.

Deliberately not exhaustive: only metrics actually used somewhere in
`research_evidence/` are registered — see `docs/metric_registry.md` for
which of the spec's full listed-metric set this omits and why.
"""

from __future__ import annotations

import dataclasses
from dataclasses import dataclass
from typing import Any

from genevra.mechanisms.definitions import (
    EVOLVABILITY_PROFILE_DEFINITION,
    GENERALIZATION_DEFINITION,
    PLASTICITY_COST_DEFINITION,
    ROBUSTNESS_DEFINITION,
    MetricDefinition,
)


@dataclass(frozen=True)
class MetricRegistryEntry:
    metric_id: str
    units: str
    aggregation_level: str
    """"organism" | "generation" | "run/seed" | "condition"."""
    replication_level: str
    """The unit a cross-condition statistical claim about this metric is
    valid at — normally "seed", per Phase 16.1/17.6."""
    definition: MetricDefinition

    def to_dict(self) -> dict[str, Any]:
        payload = dataclasses.asdict(self)
        payload["definition"] = self.definition.to_dict()
        return payload


_FITNESS_DEFINITION = MetricDefinition(
    name="fitness",
    definition="The scalar reward `SurvivalResourceFitness` assigns to one organism's lifetime.",
    input_data="One organism's `LifetimeObservations` (survival time, resources collected).",
    math_definition="A weighted sum of survival steps and resources collected; see "
    "genevra.evolution.fitness.SurvivalResourceFitness.compute.",
    interpretation="Higher values mean the organism survived longer and/or gathered more "
    "resources under the tested environment; not a general biological fitness measure.",
    limitations="Specific to the one fitness function used; a different weighting would "
    "reorder organisms differently.",
    is_realized=True,
    provenance_version="genevra.evolution.fitness.v1",
)

_GENOTYPIC_DIVERSITY_DEFINITION = MetricDefinition(
    name="genotypic_diversity",
    definition="Mean pairwise Euclidean distance between controller-weight vectors in a "
    "population (or sampled pairs, above `diversity_max_pairs`).",
    input_data="A population's genomes at one generation/snapshot.",
    math_definition="mean_{(i,j) in pairs} ||weights_i - weights_j||_2",
    interpretation="Higher values indicate more standing genetic variation in the sampled "
    "population at that moment.",
    limitations="A capped random pair sample above the size threshold, not exhaustive "
    "enumeration; says nothing about which variation is adaptive.",
    is_realized=True,
    provenance_version="genevra.metrics.diversity.v1",
)

_NOVELTY_DEFINITION = MetricDefinition(
    name="instantaneous_novelty",
    definition="Mean distance from each individual's behavioral signature to its nearest "
    "neighbors in that generation's population plus the running novelty archive.",
    input_data="One generation's behavioral signatures and the accumulated novelty archive.",
    math_definition="mean_i k-nearest-neighbor distance(signature_i, archive union population)",
    interpretation="Relative to this run's own archive/population, not an absolute scale "
    "comparable across runs with different archives.",
    limitations="Sensitive to archive size/eviction policy and k; not compared across runs "
    "with different novelty-archive configurations.",
    is_realized=True,
    provenance_version="genevra.metrics.novelty.v1",
)

REGISTRY: dict[str, MetricRegistryEntry] = {
    "fitness": MetricRegistryEntry(
        metric_id="fitness",
        units="fitness units (SurvivalResourceFitness scale)",
        aggregation_level="organism -> generation mean",
        replication_level="seed",
        definition=_FITNESS_DEFINITION,
    ),
    "genotypic_diversity": MetricRegistryEntry(
        metric_id="genotypic_diversity",
        units="mean pairwise Euclidean distance (controller-weight space)",
        aggregation_level="generation (population snapshot)",
        replication_level="seed",
        definition=_GENOTYPIC_DIVERSITY_DEFINITION,
    ),
    "instantaneous_novelty": MetricRegistryEntry(
        metric_id="instantaneous_novelty",
        units="mean k-NN behavioral-signature distance",
        aggregation_level="generation (population snapshot)",
        replication_level="seed",
        definition=_NOVELTY_DEFINITION,
    ),
    "robustness": MetricRegistryEntry(
        metric_id="robustness",
        units="behavioral-signature distance / |fitness delta| (dimension-dependent)",
        aggregation_level="one sampled genotype -> seed-level mean",
        replication_level="seed",
        definition=ROBUSTNESS_DEFINITION,
    ),
    "evolvability_mean_behavioral_distance": MetricRegistryEntry(
        metric_id="evolvability_mean_behavioral_distance",
        units="mean behavioral-signature distance across a one-step mutational neighborhood",
        aggregation_level="one sampled genotype -> seed-level value",
        replication_level="seed",
        definition=EVOLVABILITY_PROFILE_DEFINITION,
    ),
    "plasticity_cost_association": MetricRegistryEntry(
        metric_id="plasticity_cost_association",
        units="Pearson correlation coefficient (dimensionless, [-1, 1])",
        aggregation_level="sampled genotypes -> single correlation",
        replication_level="n/a (correlational, not a seed-level replicated comparison)",
        definition=PLASTICITY_COST_DEFINITION,
    ),
    "generalization_retention": MetricRegistryEntry(
        metric_id="generalization_retention",
        units="ratio (fitness in category / fitness in train)",
        aggregation_level="one sampled genotype per environment category",
        replication_level="seed",
        definition=GENERALIZATION_DEFINITION,
    ),
}

__all__ = ["MetricRegistryEntry", "REGISTRY"]
