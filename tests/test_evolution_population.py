import numpy as np
import pytest

from genevra.evolution.population import Population, PopulationConfig
from genevra.organism.genome import ControllerArchitecture
from genevra.organism.organism import OrganismConfig
from genevra.simulation.types import Action


def make_config(size: int = 5) -> PopulationConfig:
    arch = ControllerArchitecture(input_size=10, hidden_size=4, output_size=len(Action))
    organism_config = OrganismConfig(view_radius=1, memory_size=2, initial_energy=10.0)
    return PopulationConfig(size=size, architecture=arch, organism_config=organism_config)


def test_initialize_creates_requested_population_size() -> None:
    population = Population(make_config(size=7))
    population.initialize(np.random.default_rng(0))
    assert population.size == 7


def test_individual_ids_are_unique_and_sequential() -> None:
    population = Population(make_config(size=5))
    population.initialize(np.random.default_rng(0))
    ids = [ind.id for ind in population.individuals]
    assert ids == sorted(ids)
    assert len(set(ids)) == len(ids)


def test_founders_have_generation_zero_and_no_parents() -> None:
    population = Population(make_config(size=3))
    population.initialize(np.random.default_rng(0))
    for individual in population.individuals:
        assert individual.generation == 0
        assert individual.parent_ids == ()


def test_new_offspring_gets_a_fresh_id_and_recorded_parent() -> None:
    population = Population(make_config(size=3))
    population.initialize(np.random.default_rng(0))
    last_id = population.individuals[-1].id
    offspring = population.new_offspring(
        population.individuals[0].genome, generation=1, parent_ids=(0,)
    )
    assert offspring.id == last_id + 1
    assert offspring.generation == 1
    assert offspring.parent_ids == (0,)


def test_initial_mutation_genes_are_applied_to_founders() -> None:
    config = make_config(size=3)
    population = Population(config)
    population.initialize(np.random.default_rng(0))
    for individual in population.individuals:
        assert individual.genome.mutation_genes[0] == config.initial_mutation_rate
        assert individual.genome.mutation_genes[1] == config.initial_mutation_sigma


def test_config_rejects_output_size_mismatched_with_action_space() -> None:
    arch = ControllerArchitecture(input_size=10, hidden_size=4, output_size=3)
    organism_config = OrganismConfig(view_radius=1, memory_size=2, initial_energy=10.0)
    with pytest.raises(ValueError):
        PopulationConfig(size=5, architecture=arch, organism_config=organism_config)


def test_config_rejects_nonpositive_size() -> None:
    arch = ControllerArchitecture(input_size=10, hidden_size=4, output_size=len(Action))
    organism_config = OrganismConfig(view_radius=1, memory_size=2, initial_energy=10.0)
    with pytest.raises(ValueError):
        PopulationConfig(size=0, architecture=arch, organism_config=organism_config)
