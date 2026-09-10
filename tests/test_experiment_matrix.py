import dataclasses
from collections.abc import Callable

import pytest

from genevra.analysis.comparison import ComparisonRunner
from genevra.evolution.engine import EvolutionConfig
from genevra.evolution.fitness import SurvivalResourceFitness
from genevra.evolution.population import PopulationConfig
from genevra.evolution.reproduction import PopulationReproductionConfig
from genevra.evolution.selection import TournamentSelection
from genevra.experiments.config import ExperimentConfig
from genevra.experiments.matrix import build_experiment_matrix
from genevra.organism.genome import ControllerArchitecture
from genevra.organism.learning import NoLearning
from genevra.organism.mutation import GaussianMutation
from genevra.organism.organism import OrganismConfig
from genevra.simulation.grid_world import GridWorldConfig
from genevra.simulation.types import Action

_VIEW_RADIUS = 1
_MEMORY_SIZE = 2
_INPUT_SIZE = (2 * _VIEW_RADIUS + 1) ** 2 * 2 + 2 + _MEMORY_SIZE


def _base_config_factory(seed: int) -> ExperimentConfig:
    architecture = ControllerArchitecture(
        input_size=_INPUT_SIZE, hidden_size=5, output_size=len(Action)
    )
    organism_config = OrganismConfig(
        view_radius=_VIEW_RADIUS, memory_size=_MEMORY_SIZE, initial_energy=15.0
    )
    population_config = PopulationConfig(
        size=5, architecture=architecture, organism_config=organism_config
    )
    environment_config = GridWorldConfig(width=8, height=8, view_radius=_VIEW_RADIUS, max_steps=10)
    evolution_config = EvolutionConfig(
        generations=2,
        steps_per_lifetime=10,
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
    return ExperimentConfig(name="base", evolution=evolution_config)


def _double_generations(evolution: EvolutionConfig) -> EvolutionConfig:
    return dataclasses.replace(evolution, generations=evolution.generations * 2)


_CONDITIONS: dict[str, Callable[[EvolutionConfig], EvolutionConfig]] = {
    "short": lambda e: e,
    "long": _double_generations,
}


def test_matrix_generates_one_cell_per_condition() -> None:
    matrix = build_experiment_matrix(_base_config_factory, _CONDITIONS, seeds=[0, 1])
    assert set(matrix.conditions.keys()) == {"short", "long"}
    assert matrix.total_runs == 4
    assert matrix.truncated is False


def test_matrix_crosses_conditions_with_environment_regimes() -> None:
    regimes = {
        "small": GridWorldConfig(width=6, height=6, view_radius=_VIEW_RADIUS, max_steps=10),
        "large": GridWorldConfig(width=12, height=12, view_radius=_VIEW_RADIUS, max_steps=10),
    }
    matrix = build_experiment_matrix(
        _base_config_factory, _CONDITIONS, seeds=[0], environment_regimes=regimes
    )
    assert set(matrix.conditions.keys()) == {
        "short__small",
        "short__large",
        "long__small",
        "long__large",
    }


def test_matrix_seeds_are_shared_deterministically_across_cells() -> None:
    matrix = build_experiment_matrix(_base_config_factory, _CONDITIONS, seeds=[3, 4, 5])
    result = ComparisonRunner(conditions=matrix.conditions, seeds=matrix.seeds).run()
    seeds_short = [r["seed"] for r in result.conditions["short"]]
    seeds_long = [r["seed"] for r in result.conditions["long"]]
    assert seeds_short == seeds_long == [3, 4, 5]


def test_matrix_applies_the_condition_transform() -> None:
    matrix = build_experiment_matrix(_base_config_factory, _CONDITIONS, seeds=[0])
    short_config = matrix.conditions["short"](0)
    long_config = matrix.conditions["long"](0)
    assert long_config.evolution.generations == short_config.evolution.generations * 2


def test_matrix_truncates_deterministically_when_over_budget() -> None:
    matrix = build_experiment_matrix(
        _base_config_factory, _CONDITIONS, seeds=[0, 1, 2, 3, 4], max_runs=4
    )
    assert matrix.truncated is True
    assert matrix.total_runs <= 4
    assert matrix.warnings != ()


def test_matrix_rejects_empty_conditions_or_seeds() -> None:
    with pytest.raises(ValueError):
        build_experiment_matrix(_base_config_factory, {}, seeds=[0])
    with pytest.raises(ValueError):
        build_experiment_matrix(_base_config_factory, _CONDITIONS, seeds=[])
