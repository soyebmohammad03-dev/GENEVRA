import dataclasses
from collections.abc import Callable

import pytest

from genevra.analysis.comparison import ComparisonRunner, validate_comparison
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


# Module-level (not a closure) so it is picklable for the parallel executor.
def _picklable_condition_factory(seed: int) -> ExperimentConfig:
    architecture = ControllerArchitecture(
        input_size=_INPUT_SIZE, hidden_size=5, output_size=len(Action)
    )
    organism_config = OrganismConfig(
        view_radius=_VIEW_RADIUS, memory_size=_MEMORY_SIZE, initial_energy=15.0
    )
    population_config = PopulationConfig(
        size=5, architecture=architecture, organism_config=organism_config
    )
    environment_config = GridWorldConfig(width=8, height=8, view_radius=_VIEW_RADIUS, max_steps=15)
    evolution_config = EvolutionConfig(
        generations=2,
        steps_per_lifetime=15,
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


def test_parallel_execution_matches_sequential_execution() -> None:
    sequential = ComparisonRunner(
        conditions={"a": _picklable_condition_factory, "b": _picklable_condition_factory},
        seeds=[0, 1, 2],
    ).run(parallel=False)
    parallel = ComparisonRunner(
        conditions={"a": _picklable_condition_factory, "b": _picklable_condition_factory},
        seeds=[0, 1, 2],
    ).run(parallel=True, max_workers=2)

    assert set(parallel.conditions.keys()) == set(sequential.conditions.keys())
    for name in sequential.conditions:
        seq_by_seed = {r["seed"]: r["trajectory"] for r in sequential.conditions[name]}
        par_by_seed = {r["seed"]: r["trajectory"] for r in parallel.conditions[name]}
        assert seq_by_seed.keys() == par_by_seed.keys()
        for seed in seq_by_seed:
            # Deterministic per seed: parallel execution must reproduce
            # exactly what sequential execution produces for that seed.
            assert seq_by_seed[seed] == par_by_seed[seed]


def test_parallel_execution_preserves_seed_and_condition_identity() -> None:
    result = ComparisonRunner(
        conditions={"a": _picklable_condition_factory, "b": _picklable_condition_factory},
        seeds=[10, 11, 12],
    ).run(parallel=True, max_workers=3)
    for name, runs in result.conditions.items():
        seeds_seen = sorted(r["seed"] for r in runs)
        assert seeds_seen == [10, 11, 12]
        for run in runs:
            assert run["condition_id"] == name


class _AlwaysFailingFitness:
    """A `FitnessFunction` that always raises — used only for the
    poisoned seed-1 config, to check that one run's in-engine failure
    doesn't corrupt sibling runs."""

    def compute(self, observations: object) -> float:
        raise RuntimeError("boom")


def _factory_that_fails_for_seed_one(seed: int) -> ExperimentConfig:
    config = _picklable_condition_factory(seed)
    if seed != 1:
        return config
    evolution = config.evolution
    poisoned_evolution = EvolutionConfig(
        generations=evolution.generations,
        steps_per_lifetime=evolution.steps_per_lifetime,
        environment_config=evolution.environment_config,
        population_config=evolution.population_config,
        fitness_function=_AlwaysFailingFitness(),
        selection_strategy=evolution.selection_strategy,
        reproduction=evolution.reproduction,
        learning_rule_factory=evolution.learning_rule_factory,
        seed=seed,
    )
    return ExperimentConfig(name=config.name, evolution=poisoned_evolution)


def test_parallel_execution_failure_does_not_corrupt_other_runs() -> None:
    result = ComparisonRunner(
        conditions={"a": _factory_that_fails_for_seed_one}, seeds=[0, 1, 2]
    ).run(parallel=True)
    by_seed = {r["seed"]: r for r in result.conditions["a"]}
    assert by_seed[1]["status"] == "failed"
    assert by_seed[1]["failure"] is not None
    assert by_seed[0]["status"] == "completed"
    assert by_seed[2]["status"] == "completed"


def test_validate_comparison_reports_no_errors_for_a_healthy_comparison() -> None:
    result = ComparisonRunner(
        conditions={"a": make_config_factory(10), "b": make_config_factory(10)}, seeds=[0, 1]
    ).run()
    validation = validate_comparison(result)
    assert validation.ok()
    assert validation.errors == ()


def test_validate_comparison_flags_failed_runs_as_a_warning_not_silently() -> None:
    result = ComparisonRunner(
        conditions={"a": _factory_that_fails_for_seed_one}, seeds=[0, 1, 2]
    ).run()
    validation = validate_comparison(result)
    assert validation.ok()  # a failed run alone is a warning, not a critical error
    assert any("failed run" in w for w in validation.warnings)


def test_validate_comparison_errors_on_missing_seed_for_one_condition() -> None:
    result = ComparisonRunner(
        conditions={"a": make_config_factory(10), "b": make_config_factory(10)}, seeds=[0, 1]
    ).run()
    # Simulate a condition silently missing one seed's run.
    tampered = dataclasses.replace(
        result, conditions={**result.conditions, "b": result.conditions["b"][:1]}
    )
    validation = validate_comparison(tampered)
    assert not validation.ok()
    assert any("missing runs" in e for e in validation.errors)
    assert any("different numbers of runs" in e for e in validation.errors)
