import numpy as np
import pytest

from genevra.organism.genome import ControllerArchitecture, Genome


def make_architecture() -> ControllerArchitecture:
    return ControllerArchitecture(input_size=4, hidden_size=3, output_size=2)


def test_num_params_matches_weight_layout() -> None:
    arch = make_architecture()
    # W1 (3x4) + b1 (3) + W2 (2x3) + b2 (2)
    assert arch.num_params == (4 * 3 + 3) + (3 * 2 + 2)


def test_random_genome_has_correct_shapes() -> None:
    arch = make_architecture()
    rng = np.random.default_rng(0)
    genome = Genome.random(arch, rng)
    assert genome.controller_weights.shape == (arch.num_params,)
    assert genome.metabolic_genes.shape == (4,)
    assert genome.mutation_genes.shape == (2,)
    assert genome.learning_genes.shape == (3,)


def test_genome_rejects_wrong_shaped_arrays() -> None:
    arch = make_architecture()
    with pytest.raises(ValueError):
        Genome(
            architecture=arch,
            controller_weights=np.zeros(3, dtype=np.float32),  # wrong size
            metabolic_genes=np.zeros(4, dtype=np.float32),
            mutation_genes=np.zeros(2, dtype=np.float32),
            learning_genes=np.zeros(3, dtype=np.float32),
        )


def test_architecture_rejects_nonpositive_sizes() -> None:
    with pytest.raises(ValueError):
        ControllerArchitecture(input_size=0, hidden_size=3, output_size=2)


def test_genome_is_genotype_distinct_from_phenotype() -> None:
    from genevra.organism.phenotype import develop

    arch = make_architecture()
    rng = np.random.default_rng(0)
    genome = Genome.random(arch, rng)
    phenotype = develop(genome)
    assert not hasattr(phenotype, "controller_weights")
    assert phenotype.controller.weight1.shape == (arch.hidden_size, arch.input_size)
