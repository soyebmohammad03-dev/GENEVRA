import numpy as np

from genevra.evolution.reproduction import PopulationReproduction, PopulationReproductionConfig
from genevra.organism.genome import ControllerArchitecture, Genome
from genevra.organism.mutation import GaussianMutation


def make_genome() -> Genome:
    arch = ControllerArchitecture(input_size=4, hidden_size=3, output_size=2)
    genome = Genome.random(arch, np.random.default_rng(0))
    genome.mutation_genes[:] = [1.0, 0.5]  # mutate everything, visibly
    return genome


def make_reproduction(energy_threshold: float = 5.0) -> PopulationReproduction:
    config = PopulationReproductionConfig(
        energy_threshold=energy_threshold, mutation_operator=GaussianMutation()
    )
    return PopulationReproduction(config)


def test_eligible_parent_indices_respects_energy_threshold() -> None:
    reproduction = make_reproduction(energy_threshold=5.0)
    eligible = reproduction.eligible_parent_indices([1.0, 5.0, 10.0, 4.9])
    assert eligible == [1, 2]


def test_no_eligible_parents_when_all_below_threshold() -> None:
    reproduction = make_reproduction(energy_threshold=100.0)
    assert reproduction.eligible_parent_indices([1.0, 2.0, 3.0]) == []


def test_parent_genome_is_never_mutated_by_reproduction() -> None:
    """Critical invariant: producing an offspring must never alter the
    parent's own genome arrays, even though mutation_genes is set to
    mutate every element."""
    reproduction = make_reproduction()
    parent_genome = make_genome()
    original_controller_weights = parent_genome.controller_weights.copy()
    original_metabolic_genes = parent_genome.metabolic_genes.copy()

    offspring_genome = reproduction.produce_offspring_genome(
        parent_genome, np.random.default_rng(1)
    )

    assert np.array_equal(parent_genome.controller_weights, original_controller_weights)
    assert np.array_equal(parent_genome.metabolic_genes, original_metabolic_genes)
    assert parent_genome.controller_weights is not offspring_genome.controller_weights

    # Mutating the offspring's arrays in place must not touch the parent's.
    offspring_genome.controller_weights[0] = 999.0
    assert parent_genome.controller_weights[0] != 999.0


def test_offspring_genome_differs_from_parent_when_mutation_rate_is_high() -> None:
    reproduction = make_reproduction()
    parent_genome = make_genome()
    offspring_genome = reproduction.produce_offspring_genome(
        parent_genome, np.random.default_rng(1)
    )
    assert not np.array_equal(offspring_genome.controller_weights, parent_genome.controller_weights)
