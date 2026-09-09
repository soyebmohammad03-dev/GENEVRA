import json

from genevra.evolution.engine import EvolutionConfig
from genevra.evolution.fitness import SurvivalResourceFitness
from genevra.evolution.population import PopulationConfig
from genevra.evolution.reproduction import PopulationReproductionConfig
from genevra.evolution.selection import TournamentSelection
from genevra.experiments.config import ExperimentConfig
from genevra.experiments.runner import ExperimentRunner
from genevra.organism.genome import ControllerArchitecture
from genevra.organism.learning import NoLearning
from genevra.organism.mutation import GaussianMutation
from genevra.organism.organism import OrganismConfig
from genevra.simulation.grid_world import GridWorldConfig
from genevra.simulation.types import Action

_VIEW_RADIUS = 1
_MEMORY_SIZE = 2
_INPUT_SIZE = (2 * _VIEW_RADIUS + 1) ** 2 * 2 + 2 + _MEMORY_SIZE


def make_experiment_config(seed: int) -> ExperimentConfig:
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
    evolution_config = EvolutionConfig(
        generations=2,
        steps_per_lifetime=20,
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
    return ExperimentConfig(name="test-experiment", evolution=evolution_config)


def test_runner_produces_a_self_contained_result() -> None:
    runner = ExperimentRunner(make_experiment_config(seed=0))
    result = runner.run()
    assert result.name == "test-experiment"
    assert result.seed == 0
    assert result.status == "completed"
    assert result.generations_completed == 2
    assert len(result.trajectory) == 2
    assert result.final_population_size == 6
    assert result.software.genevra_version


def test_result_is_json_serializable() -> None:
    runner = ExperimentRunner(make_experiment_config(seed=0))
    result = runner.run()
    encoded = json.dumps(result.to_dict())
    decoded = json.loads(encoded)
    assert decoded["name"] == "test-experiment"
    assert len(decoded["trajectory"]) == 2
    assert len(decoded["lineage"]) > 0


def test_same_config_and_seed_reproduce_identical_results() -> None:
    result_a = ExperimentRunner(make_experiment_config(seed=7)).run()
    result_b = ExperimentRunner(make_experiment_config(seed=7)).run()
    assert result_a.to_dict()["trajectory"] == result_b.to_dict()["trajectory"]
    assert result_a.to_dict()["lineage"] == result_b.to_dict()["lineage"]


def test_different_seeds_can_produce_different_results() -> None:
    result_a = ExperimentRunner(make_experiment_config(seed=1)).run()
    result_b = ExperimentRunner(make_experiment_config(seed=2)).run()
    assert result_a.to_dict()["trajectory"] != result_b.to_dict()["trajectory"]


def test_runner_exposes_the_underlying_engine_after_run() -> None:
    runner = ExperimentRunner(make_experiment_config(seed=0))
    assert runner.engine is None
    runner.run()
    assert runner.engine is not None
    assert runner.engine.generation == 2
