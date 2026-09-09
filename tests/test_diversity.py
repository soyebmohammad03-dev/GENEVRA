import numpy as np
import pytest

from genevra.metrics.diversity import (
    CosineDistance,
    EuclideanDistance,
    behavioral_diversity,
    genotypic_diversity,
    mean_pairwise_distance,
)
from genevra.organism.genome import ControllerArchitecture, Genome


def test_euclidean_distance() -> None:
    a = np.array([0.0, 0.0], dtype=np.float32)
    b = np.array([3.0, 4.0], dtype=np.float32)
    assert EuclideanDistance().distance(a, b) == 5.0


def test_cosine_distance_of_identical_vectors_is_zero() -> None:
    a = np.array([1.0, 2.0, 3.0], dtype=np.float32)
    assert CosineDistance().distance(a, a) == pytest.approx(0.0, abs=1e-6)


def test_cosine_distance_handles_zero_vector() -> None:
    zero = np.zeros(3, dtype=np.float32)
    other = np.array([1.0, 0.0, 0.0], dtype=np.float32)
    assert CosineDistance().distance(zero, other) == 1.0


def test_mean_pairwise_distance_of_fewer_than_two_vectors_is_zero() -> None:
    assert mean_pairwise_distance([]) == 0.0
    assert mean_pairwise_distance([np.zeros(3, dtype=np.float32)]) == 0.0


def test_mean_pairwise_distance_of_identical_vectors_is_zero() -> None:
    vectors = [np.ones(3, dtype=np.float32) for _ in range(4)]
    assert mean_pairwise_distance(vectors) == 0.0


def test_genotypic_diversity_increases_with_spread_genomes() -> None:
    arch = ControllerArchitecture(input_size=4, hidden_size=3, output_size=2)
    tight = [Genome.random(arch, np.random.default_rng(0)) for _ in range(5)]
    for genome in tight[1:]:
        genome.controller_weights[:] = tight[0].controller_weights  # collapse to identical
    spread = [Genome.random(arch, np.random.default_rng(seed)) for seed in range(5)]

    assert genotypic_diversity(tight) == 0.0
    assert genotypic_diversity(spread) > genotypic_diversity(tight)


def test_behavioral_diversity_is_a_separate_computation_from_genotypic() -> None:
    """Two identical genomes can still have distinct behavioral
    signatures — genotypic and behavioral diversity must not collapse
    into the same number by construction."""
    signatures = [
        np.array([1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0], dtype=np.float32),
        np.array([0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0], dtype=np.float32),
    ]
    genomes = [
        Genome.random(ControllerArchitecture(4, 3, 2), np.random.default_rng(0)) for _ in range(2)
    ]
    for genome in genomes[1:]:
        genome.controller_weights[:] = genomes[0].controller_weights

    assert genotypic_diversity(genomes) == 0.0
    assert behavioral_diversity(signatures) > 0.0


def test_max_pairs_requires_rng_when_subsampling() -> None:
    vectors = [np.random.default_rng(i).random(3).astype(np.float32) for i in range(5)]
    with pytest.raises(ValueError):
        mean_pairwise_distance(vectors, max_pairs=2)
