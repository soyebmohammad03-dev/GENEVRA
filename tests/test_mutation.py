import numpy as np

from genevra.organism.genome import ControllerArchitecture, Genome
from genevra.organism.mutation import GaussianMutation


def make_genome(mutation_rate: float = 1.0, mutation_sigma: float = 0.5) -> Genome:
    arch = ControllerArchitecture(input_size=4, hidden_size=3, output_size=2)
    rng = np.random.default_rng(0)
    genome = Genome.random(arch, rng)
    genome.mutation_genes[:] = [mutation_rate, mutation_sigma]
    return genome


def test_mutation_is_reproducible_given_same_seed() -> None:
    genome = make_genome()
    mutator = GaussianMutation()
    child_a = mutator.mutate(genome, np.random.default_rng(123))
    child_b = mutator.mutate(genome, np.random.default_rng(123))
    assert np.array_equal(child_a.controller_weights, child_b.controller_weights)
    assert np.array_equal(child_a.mutation_genes, child_b.mutation_genes)


def test_different_rng_state_produces_different_offspring() -> None:
    genome = make_genome()
    mutator = GaussianMutation()
    child_a = mutator.mutate(genome, np.random.default_rng(1))
    child_b = mutator.mutate(genome, np.random.default_rng(2))
    assert not np.array_equal(child_a.controller_weights, child_b.controller_weights)


def test_zero_mutation_rate_leaves_genes_unchanged() -> None:
    genome = make_genome(mutation_rate=0.0)
    mutator = GaussianMutation()
    child = mutator.mutate(genome, np.random.default_rng(0))
    assert np.array_equal(child.controller_weights, genome.controller_weights)
    assert np.array_equal(child.metabolic_genes, genome.metabolic_genes)
    assert np.array_equal(child.learning_genes, genome.learning_genes)


def test_mutation_rate_is_read_from_genome_not_hardcoded() -> None:
    """Two genomes with identical values but different heritable
    mutation_genes must mutate by different amounts under the same RNG."""
    low_rate_genome = make_genome(mutation_rate=0.0, mutation_sigma=0.5)
    high_rate_genome = make_genome(mutation_rate=1.0, mutation_sigma=0.5)
    mutator = GaussianMutation()

    low_child = mutator.mutate(low_rate_genome, np.random.default_rng(0))
    high_child = mutator.mutate(high_rate_genome, np.random.default_rng(0))

    assert np.array_equal(low_child.controller_weights, low_rate_genome.controller_weights)
    assert not np.array_equal(high_child.controller_weights, high_rate_genome.controller_weights)


def test_mutation_genes_themselves_can_drift() -> None:
    genome = make_genome(mutation_rate=0.5, mutation_sigma=0.3)
    mutator = GaussianMutation()
    child = mutator.mutate(genome, np.random.default_rng(0))
    assert child.mutation_genes.shape == genome.mutation_genes.shape
    assert 0.0 <= child.mutation_genes[0] <= 1.0
    assert child.mutation_genes[1] > 0.0
