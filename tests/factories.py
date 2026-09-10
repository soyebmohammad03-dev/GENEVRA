"""Shared test-only config factories, reused across multiple test
modules (e.g. `test_comparison.py`, `test_report.py`). Kept out of any
single test module so no test file needs to import from another test
module — a proper home for cross-test-module fixtures, not production
code."""

from __future__ import annotations

from collections.abc import Callable

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

VIEW_RADIUS = 1
MEMORY_SIZE = 2
INPUT_SIZE = (2 * VIEW_RADIUS + 1) ** 2 * 2 + 2 + MEMORY_SIZE


def make_config_factory(max_steps: int) -> Callable[[int], ExperimentConfig]:
    def factory(seed: int) -> ExperimentConfig:
        architecture = ControllerArchitecture(
            input_size=INPUT_SIZE, hidden_size=5, output_size=len(Action)
        )
        organism_config = OrganismConfig(
            view_radius=VIEW_RADIUS, memory_size=MEMORY_SIZE, initial_energy=15.0
        )
        population_config = PopulationConfig(
            size=5, architecture=architecture, organism_config=organism_config
        )
        environment_config = GridWorldConfig(
            width=8, height=8, view_radius=VIEW_RADIUS, max_steps=max_steps
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
