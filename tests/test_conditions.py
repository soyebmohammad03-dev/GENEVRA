import dataclasses

import pytest

from genevra.evolution.engine import EvolutionConfig, EvolutionEngine
from genevra.evolution.fitness import SurvivalResourceFitness
from genevra.evolution.population import PopulationConfig
from genevra.evolution.reproduction import PopulationReproductionConfig
from genevra.evolution.selection import TournamentSelection
from genevra.experiments.conditions import (
    AblationConfig,
    LearningCondition,
    apply_ablations,
    apply_learning_condition,
)
from genevra.organism.genome import ControllerArchitecture
from genevra.organism.learning import HebbianLearning, NoLearning
from genevra.organism.mutation import GaussianMutation
from genevra.organism.organism import OrganismConfig
from genevra.simulation.dynamics import EnvironmentRegime, PeriodicDynamics, StaticDynamics
from genevra.simulation.grid_world import GridWorldConfig
from genevra.simulation.types import Action

_VIEW_RADIUS = 1
_MEMORY_SIZE = 2
_INPUT_SIZE = (2 * _VIEW_RADIUS + 1) ** 2 * 2 + 2 + _MEMORY_SIZE


def make_base_config(seed: int = 0) -> EvolutionConfig:
    architecture = ControllerArchitecture(
        input_size=_INPUT_SIZE, hidden_size=5, output_size=len(Action)
    )
    organism_config = OrganismConfig(
        view_radius=_VIEW_RADIUS, memory_size=_MEMORY_SIZE, initial_energy=15.0
    )
    population_config = PopulationConfig(
        size=6, architecture=architecture, organism_config=organism_config
    )
    environment_config = GridWorldConfig(width=9, height=9, view_radius=_VIEW_RADIUS, max_steps=20)
    return EvolutionConfig(
        generations=3,
        steps_per_lifetime=20,
        environment_config=environment_config,
        population_config=population_config,
        fitness_function=SurvivalResourceFitness(),
        selection_strategy=TournamentSelection(tournament_size=3),
        reproduction=PopulationReproductionConfig(
            energy_threshold=-1000.0, mutation_operator=GaussianMutation()
        ),
        learning_rule_factory=NoLearning,
        seed=seed,
    )


def test_no_learning_condition_uses_no_learning_rule() -> None:
    config = apply_learning_condition(make_base_config(), LearningCondition.NO_LEARNING)
    assert config.learning_rule_factory is NoLearning


def test_fixed_learning_condition_disables_learning_gene_mutation() -> None:
    config = apply_learning_condition(make_base_config(), LearningCondition.FIXED_LEARNING)
    assert config.learning_rule_factory is HebbianLearning
    mutator = config.reproduction.mutation_operator
    assert isinstance(mutator, GaussianMutation)
    assert mutator.mutate_learning_genes is False


def test_evolvable_learning_condition_enables_learning_gene_mutation() -> None:
    config = apply_learning_condition(make_base_config(), LearningCondition.EVOLVABLE_LEARNING)
    mutator = config.reproduction.mutation_operator
    assert isinstance(mutator, GaussianMutation)
    assert mutator.mutate_learning_genes is True


def test_conditions_only_differ_in_learning_not_everything_else() -> None:
    base = make_base_config()
    no_learning = apply_learning_condition(base, LearningCondition.NO_LEARNING)
    evolvable = apply_learning_condition(base, LearningCondition.EVOLVABLE_LEARNING)
    assert no_learning.generations == evolvable.generations == base.generations
    assert no_learning.population_config is base.population_config
    assert evolvable.population_config is base.population_config
    assert no_learning.environment_config is base.environment_config


def test_three_conditions_produce_distinguishable_runs_on_same_seed() -> None:
    base = make_base_config(seed=0)
    results = {}
    for condition in LearningCondition:
        config = apply_learning_condition(base, condition)
        engine = EvolutionEngine(config)
        trajectory = engine.run()
        results[condition] = [s.fitness_summary.mean for s in trajectory.snapshots]
    # Not asserting one condition "wins" — just that the mechanism actually
    # produces different runs, which is the whole point of having conditions.
    assert results[LearningCondition.NO_LEARNING] != results[LearningCondition.EVOLVABLE_LEARNING]


def test_apply_learning_condition_rejects_non_gaussian_mutation_operator() -> None:
    class _CustomOperator:
        def mutate(self, genome, rng):  # type: ignore[no-untyped-def]
            return genome

    base = make_base_config()
    bad_reproduction = dataclasses.replace(base.reproduction, mutation_operator=_CustomOperator())
    bad_config = dataclasses.replace(base, reproduction=bad_reproduction)
    with pytest.raises(TypeError):
        apply_learning_condition(bad_config, LearningCondition.EVOLVABLE_LEARNING)


def test_ablation_disable_learning_matches_no_learning_condition() -> None:
    base = make_base_config()
    ablated = apply_ablations(base, AblationConfig(learning=False))
    assert ablated.learning_rule_factory is NoLearning


def test_ablation_disable_heritable_mutation_strength() -> None:
    base = make_base_config()
    ablated = apply_ablations(base, AblationConfig(heritable_mutation_strength=False))
    mutator = ablated.reproduction.mutation_operator
    assert isinstance(mutator, GaussianMutation)
    assert mutator.mutate_mutation_genes is False


def test_ablation_disable_changing_environment_forces_static_dynamics() -> None:
    base_environment = GridWorldConfig(
        width=9,
        height=9,
        view_radius=_VIEW_RADIUS,
        max_steps=20,
        dynamics=PeriodicDynamics(
            regime_a=EnvironmentRegime(resource_regen_prob=0.5),
            regime_b=EnvironmentRegime(resource_regen_prob=0.0),
            period=10,
        ),
    )
    base = dataclasses.replace(make_base_config(), environment_config=base_environment)
    ablated = apply_ablations(base, AblationConfig(changing_environment=False))
    assert isinstance(ablated.environment_config.dynamics, StaticDynamics)


def test_ablation_defaults_leave_config_functionally_unchanged() -> None:
    base = make_base_config()
    ablated = apply_ablations(base, AblationConfig())
    assert ablated.learning_rule_factory is base.learning_rule_factory
    mutator = ablated.reproduction.mutation_operator
    assert isinstance(mutator, GaussianMutation)
    assert mutator.mutate_learning_genes is True
    assert mutator.mutate_mutation_genes is True
