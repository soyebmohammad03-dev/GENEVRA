from collections.abc import Callable

import pytest

from genevra.analysis.comparison import ComparisonRunner
from genevra.evolution.engine import EvolutionConfig
from genevra.evolution.fitness import SurvivalResourceFitness
from genevra.evolution.population import PopulationConfig
from genevra.evolution.reproduction import PopulationReproductionConfig
from genevra.evolution.selection import TournamentSelection
from genevra.experiments.config import ExperimentConfig
from genevra.organism.genome import ControllerArchitecture
from genevra.organism.learning import NoLearning
from genevra.organism.mutation import GaussianMutation
from genevra.organism.organism import OrganismConfig
from genevra.simulation.grid_world import GridWorldConfig
from genevra.simulation.types import Action

_VIEW_RADIUS = 1
_MEMORY_SIZE = 2
_INPUT_SIZE = (2 * _VIEW_RADIUS + 1) ** 2 * 2 + 2 + _MEMORY_SIZE


def make_config_factory(max_steps: int) -> Callable[[int], ExperimentConfig]:
    def factory(seed: int) -> ExperimentConfig:
        architecture = ControllerArchitecture(
            input_size=_INPUT_SIZE, hidden_size=5, output_size=len(Action)
        )
        organism_config = OrganismConfig(
            view_radius=_VIEW_RADIUS, memory_size=_MEMORY_SIZE, initial_energy=15.0
        )
        population_config = PopulationConfig(
            size=5, architecture=architecture, organism_config=organism_config
        )
        environment_config = GridWorldConfig(
            width=8, height=8, view_radius=_VIEW_RADIUS, max_steps=max_steps
        )
        evolution_config = EvolutionConfig(
            generations=2,
            steps_per_lifetime=max_steps,
            environment_config=environment_config,
            population_config=population_config,
            fitness_function=SurvivalResourceFitness(),
            selection_strategy=TournamentSelection(tournament_size=2),
            reproduction=PopulationReproductionConfig(
                energy_threshold=-1000.0, mutation_operator=GaussianMutation()
            ),
            learning_rule_factory=NoLearning,
            seed=seed,
        )
        return ExperimentConfig(name="cond", evolution=evolution_config)

    return factory


def test_comparison_runs_every_condition_across_every_seed() -> None:
    runner = ComparisonRunner(
        conditions={"short": make_config_factory(10), "long": make_config_factory(30)},
        seeds=[0, 1, 2],
    )
    result = runner.run()
    assert set(result.conditions.keys()) == {"short", "long"}
    assert len(result.conditions["short"]) == 3
    assert len(result.conditions["long"]) == 3


def test_conditions_use_the_same_seed_sequence() -> None:
    runner = ComparisonRunner(
        conditions={"a": make_config_factory(10), "b": make_config_factory(10)}, seeds=[5, 6]
    )
    result = runner.run()
    seeds_a = [r["seed"] for r in result.conditions["a"]]
    seeds_b = [r["seed"] for r in result.conditions["b"]]
    assert seeds_a == seeds_b == [5, 6]


def test_conditions_actually_differ_only_in_intended_variable() -> None:
    runner = ComparisonRunner(
        conditions={"short": make_config_factory(10), "long": make_config_factory(50)}, seeds=[0]
    )
    result = runner.run()
    short_result = result.conditions["short"][0]
    long_result = result.conditions["long"][0]
    assert short_result["environment_summary"]["max_steps"] == 10
    assert long_result["environment_summary"]["max_steps"] == 50
    # Same seed -> both are "completed" reproducibly, neither silently failed.
    assert short_result["status"] == "completed"
    assert long_result["status"] == "completed"


def test_no_failures_reported_for_a_healthy_comparison() -> None:
    runner = ComparisonRunner(conditions={"a": make_config_factory(10)}, seeds=[0, 1])
    result = runner.run()
    assert result.failures() == []


def test_comparison_runner_rejects_empty_conditions_or_seeds() -> None:
    with pytest.raises(ValueError):
        ComparisonRunner(conditions={}, seeds=[0])
    with pytest.raises(ValueError):
        ComparisonRunner(conditions={"a": make_config_factory(10)}, seeds=[])
