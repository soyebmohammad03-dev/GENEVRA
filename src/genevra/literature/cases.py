"""Phase 11.10: initial literature-inspired experiment templates.

**These are templates, not claims that GENEVRA has reproduced any paper.**
Each case below states, in its `LiteratureClaim.genevra_mapping` and its
`LiteratureExperimentSpec.approximation_notes`, exactly where GENEVRA's
model departs from the source paper's — dependent variables here are
GENEVRA's own operational proxies for the paper's concepts, not the
paper's own measurement, wherever an exact mapping does not exist.

- CASE A: plasticity/evolvability under a changing environment, inspired
  by Cuypers, Rutten & Hogeweg (2017).
- CASE B: environmental volatility's effect on the evolution of
  plasticity, inspired by Jorritsma & van den Berg (2026).
- CASE C: history dependence / contingency of evolutionary outcomes.
- CASE D: whether an evolved learning strategy predicts future
  evolutionary change.

Every condition factory below is built the same way every other GENEVRA
experiment in this repo is (`tests/factories.py`,
`experiments/exp1_isolated_vs_shared.py`): plain `EvolutionConfig`
construction, no new engine mechanism introduced for these cases.
"""

from __future__ import annotations

from collections.abc import Callable

from genevra.evolution.engine import EvolutionConfig
from genevra.evolution.fitness import SurvivalResourceFitness
from genevra.evolution.population import PopulationConfig
from genevra.evolution.reproduction import PopulationReproductionConfig
from genevra.evolution.selection import TournamentSelection
from genevra.experiments.conditions import LearningCondition, apply_learning_condition
from genevra.experiments.config import ExperimentConfig
from genevra.literature.claims import LiteratureClaim
from genevra.literature.spec import LiteratureExperimentSpec
from genevra.metrics.trajectory import MetricsLevel
from genevra.organism.genome import ControllerArchitecture
from genevra.organism.learning import HebbianLearning, NoLearning
from genevra.organism.mutation import GaussianMutation
from genevra.organism.organism import OrganismConfig
from genevra.simulation.dynamics import EnvironmentRegime, PeriodicDynamics
from genevra.simulation.grid_world import GridWorldConfig
from genevra.simulation.types import Action

_VIEW_RADIUS = 1
_MEMORY_SIZE = 2
_INPUT_SIZE = (2 * _VIEW_RADIUS + 1) ** 2 * 2 + 2 + _MEMORY_SIZE

ConditionFactory = Callable[[int], ExperimentConfig]


def _base_evolution_config(
    seed: int,
    population_size: int,
    generations: int,
    environment_config: GridWorldConfig,
    learning_rule_factory: type = NoLearning,
    mutate_learning_genes: bool = False,
    metrics_level: MetricsLevel = MetricsLevel.STANDARD,
) -> EvolutionConfig:
    architecture = ControllerArchitecture(
        input_size=_INPUT_SIZE, hidden_size=6, output_size=len(Action)
    )
    organism_config = OrganismConfig(
        view_radius=_VIEW_RADIUS, memory_size=_MEMORY_SIZE, initial_energy=15.0
    )
    population_config = PopulationConfig(
        size=population_size, architecture=architecture, organism_config=organism_config
    )
    return EvolutionConfig(
        generations=generations,
        steps_per_lifetime=environment_config.max_steps,
        environment_config=environment_config,
        population_config=population_config,
        fitness_function=SurvivalResourceFitness(),
        selection_strategy=TournamentSelection(tournament_size=2),
        reproduction=PopulationReproductionConfig(
            energy_threshold=-1000.0,
            mutation_operator=GaussianMutation(mutate_learning_genes=mutate_learning_genes),
        ),
        learning_rule_factory=learning_rule_factory,
        seed=seed,
        metrics_level=metrics_level,
        metrics_interval=1,
    )


def _static_environment(regen_prob: float = 0.05) -> GridWorldConfig:
    return GridWorldConfig(
        width=10, height=10, view_radius=_VIEW_RADIUS, max_steps=60, resource_regen_prob=regen_prob
    )


def _changing_environment() -> GridWorldConfig:
    dynamics = PeriodicDynamics(
        regime_a=EnvironmentRegime(resource_regen_prob=0.02),
        regime_b=EnvironmentRegime(resource_regen_prob=0.12),
        period=20,
    )
    return GridWorldConfig(
        width=10, height=10, view_radius=_VIEW_RADIUS, max_steps=60, dynamics=dynamics
    )


def case_a_plasticity_evolvability_tradeoff(
    population_size: int = 16, generations: int = 20, seeds: tuple[int, ...] = tuple(range(8))
) -> tuple[LiteratureClaim, LiteratureExperimentSpec, dict[str, ConditionFactory]]:
    """CASE A, inspired by Cuypers, Rutten & Hogeweg (2017): does heritable
    phenotypic plasticity (learning) increase a population's evolvability
    under a changing environment, relative to no learning at all?

    APPROXIMATION: the source paper's "evolvability" is a property of a
    gene-regulatory-network model measured via mutational robustness of
    the developmental map; GENEVRA has no equivalent GRN. This case uses
    final-generation `genotypic_diversity` under a changing environment as
    a GENEVRA-native proxy for "the population retains exploitable genetic
    variation" — a different, weaker operationalization, not the paper's
    own metric.
    """
    claim = LiteratureClaim(
        claim_id="case_a_plasticity_evolvability_tradeoff",
        source_reference="Cuypers, Rutten & Hogeweg (2017), 'Evolution of evolvability and "
        "phenotypic plasticity in virtual cells'",
        source_year=2017,
        research_question=(
            "Does the evolution of phenotypic plasticity increase evolvability under "
            "environmental change?"
        ),
        claim_text=(
            "In the source model, populations that evolve plasticity under changing "
            "conditions maintain higher evolvability than populations that cannot "
            "plastically respond."
        ),
        independent_variable="learning_condition",
        dependent_variable="genotypic_diversity",
        environmental_regime="periodically changing resource regeneration rate",
        organism_assumptions="digital grid-world organisms with a feed-forward controller, "
        "not the source paper's virtual gene-regulatory-network cells",
        evolutionary_assumptions="tournament selection, Gaussian mutation, discrete "
        "non-overlapping generations",
        measurement_definition="final-generation genotypic_diversity "
        "(genevra.metrics.diversity), a GENEVRA-native proxy, not the source paper's "
        "mutational-robustness evolvability metric",
        expected_direction="positive",
        expected_relationship="evolvable_learning condition shows higher final "
        "genotypic_diversity than no_learning under the same changing environment",
        known_limitations=(
            "GENEVRA has no gene-regulatory-network developmental model; 'evolvability' "
            "here is approximated by standing genetic diversity, not mutational "
            "robustness.",
            "Single environmental regime (one PeriodicDynamics configuration) tested; "
            "the source paper explores a range of environmental change rates.",
        ),
        genevra_mapping=(
            "independent_variable 'learning_condition' maps to "
            "genevra.experiments.conditions.LearningCondition (NO_LEARNING vs "
            "EVOLVABLE_LEARNING); dependent_variable 'genotypic_diversity' is a proxy "
            "for the source paper's evolvability metric, not an equivalent measurement."
        ),
    )
    spec = LiteratureExperimentSpec(
        spec_id="case_a_v1",
        claim_id=claim.claim_id,
        control_condition="no_learning",
        treatment_condition="evolvable_learning",
        population_size=population_size,
        generations=generations,
        seeds=seeds,
        primary_metric="genotypic_diversity",
        statistical_test="permutation_test",
        expected_direction="positive",
        approximation_notes=(
            "genotypic_diversity is used as a proxy for the source paper's "
            "mutational-robustness evolvability metric; no gene-regulatory-network "
            "developmental model exists in GENEVRA.",
        ),
    )

    def _condition(condition: LearningCondition) -> ConditionFactory:
        def factory(seed: int) -> ExperimentConfig:
            base = _base_evolution_config(
                seed,
                population_size,
                generations,
                _changing_environment(),
                learning_rule_factory=HebbianLearning,
                mutate_learning_genes=True,
            )
            evolution = apply_learning_condition(base, condition, HebbianLearning)
            return ExperimentConfig(name=f"case_a_{condition.value}", evolution=evolution)

        return factory

    conditions = {
        "no_learning": _condition(LearningCondition.NO_LEARNING),
        "evolvable_learning": _condition(LearningCondition.EVOLVABLE_LEARNING),
    }
    return claim, spec, conditions


def case_b_volatility_and_plasticity(
    population_size: int = 16, generations: int = 20, seeds: tuple[int, ...] = tuple(range(8))
) -> tuple[LiteratureClaim, LiteratureExperimentSpec, dict[str, ConditionFactory]]:
    """CASE B, inspired by Jorritsma & van den Berg (2026): does a
    volatile environment select for a higher evolved plasticity gate than
    a static one, when learning is heritable in both conditions?

    APPROXIMATION: the source paper's model is a gene-regulatory-network
    with an explicit plasticity parameter under selection; here the
    analogous heritable quantity is GENEVRA's `plasticity_gate` learning
    gene (`genevra.organism.learning.LearningParams`, index 1 of
    `learning_genes`), read from `GenerationSnapshot.learning_gene_stats`
    (only populated at `MetricsLevel.RESEARCH`).
    """
    claim = LiteratureClaim(
        claim_id="case_b_volatility_and_plasticity",
        source_reference="Jorritsma & van den Berg (2026), 'The evolution of plasticity and "
        "evolvability in a simple gene regulatory network'",
        source_year=2026,
        research_question="Does environmental volatility select for higher evolved plasticity?",
        claim_text=(
            "In the source model, a volatile environment selects for a higher evolved "
            "plasticity parameter than a static environment."
        ),
        independent_variable="environmental_volatility",
        dependent_variable="plasticity_gate",
        environmental_regime="static resource regeneration vs. a periodic two-regime cycle",
        organism_assumptions="digital grid-world organisms with Hebbian learning, not the "
        "source paper's gene-regulatory-network model",
        evolutionary_assumptions="heritable learning genes (learning_rate, "
        "plasticity_gate, decay), mutable every generation in both conditions",
        measurement_definition="mean plasticity_gate across the final generation "
        "(GenerationSnapshot.learning_gene_stats[1].mean at MetricsLevel.RESEARCH)",
        expected_direction="positive",
        expected_relationship="the periodic (volatile) condition shows a higher mean "
        "plasticity_gate at the final generation than the static condition",
        known_limitations=(
            "GENEVRA's plasticity_gate is a scalar Hebbian learning-rate modulator, not "
            "the source paper's gene-regulatory-network plasticity parameter.",
            "Only one volatility contrast (static vs. one periodic configuration) is "
            "tested; the source paper varies volatility continuously.",
        ),
        genevra_mapping=(
            "independent_variable 'environmental_volatility' maps to static vs. "
            "PeriodicDynamics GridWorldConfig.dynamics; dependent_variable "
            "'plasticity_gate' maps to learning_genes[1], read via "
            "learning_gene_stats — an approximate analog of the source paper's "
            "plasticity parameter, not an equivalent quantity."
        ),
    )
    spec = LiteratureExperimentSpec(
        spec_id="case_b_v1",
        claim_id=claim.claim_id,
        control_condition="static",
        treatment_condition="volatile",
        population_size=population_size,
        generations=generations,
        seeds=seeds,
        primary_metric="learning_gene_stats.1.mean",
        statistical_test="permutation_test",
        expected_direction="positive",
        approximation_notes=(
            "plasticity_gate (learning_genes index 1) is GENEVRA's nearest heritable "
            "analog to the source paper's plasticity parameter; it is a Hebbian "
            "learning-rate modulator in a feed-forward controller, not a "
            "gene-regulatory-network parameter.",
        ),
    )

    def _condition(dynamics_factory: Callable[[], GridWorldConfig]) -> ConditionFactory:
        def factory(seed: int) -> ExperimentConfig:
            evolution = _base_evolution_config(
                seed,
                population_size,
                generations,
                dynamics_factory(),
                learning_rule_factory=HebbianLearning,
                mutate_learning_genes=True,
                metrics_level=MetricsLevel.RESEARCH,
            )
            return ExperimentConfig(name="case_b", evolution=evolution)

        return factory

    conditions = {
        "static": _condition(_static_environment),
        "volatile": _condition(_changing_environment),
    }
    return claim, spec, conditions


def case_c_history_dependence(
    population_size: int = 16, generations: int = 20, seeds: tuple[int, ...] = tuple(range(8))
) -> tuple[LiteratureClaim, LiteratureExperimentSpec, dict[str, ConditionFactory]]:
    """CASE C: history dependence / contingency of evolutionary outcomes —
    does a higher mutation rate (more stochastic exploration of genotype
    space early on) lead to more divergent final behavioral outcomes,
    consistent with stronger historical contingency?

    APPROXIMATION: "contingency" is properly a claim about variance of
    outcomes across replicate histories, not a claim about the mean.
    This case's control/treatment mean comparison
    (`LiteratureReproductionRunner` only implements a mean-difference
    permutation test) is a weaker, mean-based proxy for a
    variance-of-outcomes claim — documented here explicitly rather than
    silently substituted.
    """
    claim = LiteratureClaim(
        claim_id="case_c_history_dependence",
        source_reference="general contingency/history-dependence literature in "
        "experimental evolution (no single paper mapped one-to-one)",
        source_year=2017,
        research_question=(
            "Do early stochastic differences (e.g. mutation rate) produce more divergent "
            "long-run behavioral outcomes, consistent with historical contingency?"
        ),
        claim_text=(
            "Higher early mutational variation leads to more divergent evolved behavior "
            "across independent replicate histories."
        ),
        independent_variable="mutation_sigma",
        dependent_variable="behavioral_diversity",
        environmental_regime="static resource regeneration",
        organism_assumptions="digital grid-world organisms, no learning (isolates genetic "
        "contingency from lifetime plasticity)",
        evolutionary_assumptions="tournament selection, Gaussian mutation with heritable "
        "mutation strength",
        measurement_definition="final-generation behavioral_diversity, compared as a MEAN "
        "across seeds — an approximation of a variance-of-outcomes contingency claim, "
        "not the claim itself",
        expected_direction="positive",
        expected_relationship="high-mutation-sigma condition shows higher mean final "
        "behavioral_diversity than low-mutation-sigma condition",
        known_limitations=(
            "The genuine contingency claim concerns variance across replicate histories, "
            "not mean behavior; this case tests a mean-based proxy because "
            "LiteratureReproductionRunner implements a mean-difference test only.",
            "No single published paper maps to this case one-to-one; it is a "
            "GENEVRA-native operationalization of a general contingency hypothesis.",
        ),
        genevra_mapping=(
            "independent_variable 'mutation_sigma' maps to GaussianMutation's initial "
            "sigma (via mutation_genes founders); dependent_variable "
            "'behavioral_diversity' is measured as a cross-seed MEAN, not variance — an "
            "explicit approximation of the underlying contingency claim."
        ),
    )
    spec = LiteratureExperimentSpec(
        spec_id="case_c_v1",
        claim_id=claim.claim_id,
        control_condition="low_mutation",
        treatment_condition="high_mutation",
        population_size=population_size,
        generations=generations,
        seeds=seeds,
        primary_metric="behavioral_diversity",
        statistical_test="permutation_test",
        expected_direction="positive",
        approximation_notes=(
            "Tests a mean-based proxy for a variance-of-outcomes contingency claim; see "
            "known_limitations on the claim.",
        ),
    )

    def _condition(mutate_learning_genes: bool) -> ConditionFactory:
        def factory(seed: int) -> ExperimentConfig:
            evolution = _base_evolution_config(
                seed,
                population_size,
                generations,
                _static_environment(),
                learning_rule_factory=NoLearning,
                mutate_learning_genes=False,
            )
            evolution = _with_mutation_scale(evolution, mutate_learning_genes)
            return ExperimentConfig(name="case_c", evolution=evolution)

        return factory

    conditions = {"low_mutation": _condition(False), "high_mutation": _condition(True)}
    return claim, spec, conditions


def _with_mutation_scale(evolution: EvolutionConfig, high: bool) -> EvolutionConfig:
    """`high=True` scales up `PopulationConfig.initial_mutation_sigma` —
    the founder mutation-strength gene every offspring's own mutable
    `mutation_genes` then evolves from (see
    `genevra.evolution.population`)."""
    import dataclasses

    factor = 3.0 if high else 1.0
    pop = evolution.population_config
    new_pop = dataclasses.replace(
        pop, initial_mutation_sigma=pop.initial_mutation_sigma * factor
    )
    return dataclasses.replace(evolution, population_config=new_pop)


def case_d_learning_strategy_predicts_potential(
    population_size: int = 16, generations: int = 20, seeds: tuple[int, ...] = tuple(range(8))
) -> tuple[LiteratureClaim, LiteratureExperimentSpec, dict[str, ConditionFactory]]:
    """CASE D: does an evolvable learning strategy predict greater
    subsequent evolutionary change (a proxy for "future evolutionary
    potential") relative to a fixed learning strategy?

    APPROXIMATION: "future evolutionary potential" would properly be
    measured with a held-out environment shift and re-evaluated
    evolvability (see `genevra.metrics.evolvability`,
    `genevra.analysis.tradeoff`); this case instead uses the late-run
    `behavior_centroid_shift` already computed in every trajectory as a
    cheaper, weaker proxy for "how much behavioral change is still being
    produced late in the run" — documented explicitly, not substituted
    silently.
    """
    claim = LiteratureClaim(
        claim_id="case_d_learning_strategy_predicts_potential",
        source_reference="general evolvability/plasticity literature relating evolved "
        "learning strategy to future adaptive potential (no single paper mapped "
        "one-to-one)",
        source_year=2017,
        research_question=(
            "Does an evolved (evolvable) learning strategy predict greater subsequent "
            "evolutionary change than a fixed learning strategy?"
        ),
        claim_text=(
            "Populations with an evolvable learning strategy continue producing "
            "behavioral change later in a run, relative to populations with a fixed "
            "learning strategy."
        ),
        independent_variable="learning_condition",
        dependent_variable="behavior_centroid_shift",
        environmental_regime="periodically changing resource regeneration rate",
        organism_assumptions="digital grid-world organisms with Hebbian learning",
        evolutionary_assumptions="tournament selection, Gaussian mutation, discrete "
        "non-overlapping generations",
        measurement_definition="final-generation behavior_centroid_shift "
        "(genevra.metrics.trajectory.GenerationSnapshot) — a proxy for continued "
        "evolutionary change, not the source concept's proper evolvability "
        "re-measurement",
        expected_direction="positive",
        expected_relationship="evolvable_learning condition shows higher final "
        "behavior_centroid_shift than fixed_learning",
        known_limitations=(
            "A proper 'future evolutionary potential' measurement would re-run "
            "EvolvabilityAnalyzer on late-generation genotypes and/or evaluate them "
            "under a held-out environment shift; this case substitutes the cheaper, "
            "already-computed behavior_centroid_shift trajectory field instead.",
            "behavior_centroid_shift can be None on a generation with too few "
            "individuals to compute a centroid; such runs contribute no data point.",
        ),
        genevra_mapping=(
            "independent_variable 'learning_condition' maps to "
            "genevra.experiments.conditions.LearningCondition (FIXED_LEARNING vs "
            "EVOLVABLE_LEARNING); dependent_variable 'behavior_centroid_shift' is a "
            "proxy for future evolutionary potential, not an equivalent measurement."
        ),
    )
    spec = LiteratureExperimentSpec(
        spec_id="case_d_v1",
        claim_id=claim.claim_id,
        control_condition="fixed_learning",
        treatment_condition="evolvable_learning",
        population_size=population_size,
        generations=generations,
        seeds=seeds,
        primary_metric="behavior_centroid_shift",
        statistical_test="permutation_test",
        expected_direction="positive",
        approximation_notes=(
            "behavior_centroid_shift (late-run) substitutes for a proper re-measured "
            "evolvability/held-out-shift definition of 'future evolutionary potential'.",
        ),
    )

    def _condition(condition: LearningCondition) -> ConditionFactory:
        def factory(seed: int) -> ExperimentConfig:
            base = _base_evolution_config(
                seed,
                population_size,
                generations,
                _changing_environment(),
                learning_rule_factory=HebbianLearning,
                mutate_learning_genes=True,
            )
            evolution = apply_learning_condition(base, condition, HebbianLearning)
            return ExperimentConfig(name=f"case_d_{condition.value}", evolution=evolution)

        return factory

    conditions = {
        "fixed_learning": _condition(LearningCondition.FIXED_LEARNING),
        "evolvable_learning": _condition(LearningCondition.EVOLVABLE_LEARNING),
    }
    return claim, spec, conditions


__all__ = [
    "ConditionFactory",
    "case_a_plasticity_evolvability_tradeoff",
    "case_b_volatility_and_plasticity",
    "case_c_history_dependence",
    "case_d_learning_strategy_predicts_potential",
]
