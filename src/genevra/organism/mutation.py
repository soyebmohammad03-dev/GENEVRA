"""Mutation as a swappable operator, not logic embedded in reproduction.

`GaussianMutation` reads its rate and step size from the *genome being
mutated* (`genome.mutation_genes`), not from a global constant — so
mutation strength is itself heritable and, once population-level selection
exists, can be selected on. This is what makes "can evolvability evolve?"
representable at all: if mutation rate were a simulator-wide constant,
there would be nothing for evolution to act on.
"""

from __future__ import annotations

from typing import Protocol

import numpy as np

from genevra.arrays import FloatArray
from genevra.organism.genome import Genome

# ponytail: the mutation_genes themselves (rate, sigma) mutate at a small
# fixed meta-rate rather than a genome-encoded meta-rate — a fully
# heritable meta-mutation-rate is a deliberate future step, not a
# permanent ceiling.
_META_MUTATION_SIGMA = 0.02
_MUTATION_RATE_BOUNDS = (0.0, 1.0)
_MUTATION_SIGMA_BOUNDS = (1e-6, 10.0)


class MutationOperator(Protocol):
    def mutate(self, genome: Genome, rng: np.random.Generator) -> Genome: ...


class GaussianMutation:
    """Per-element Gaussian mutation: each element of each gene group is,
    independently, mutated with probability `rate` by adding
    `Normal(0, sigma)` noise, where `(rate, sigma)` come from the genome's
    own `mutation_genes`."""

    def mutate(self, genome: Genome, rng: np.random.Generator) -> Genome:
        rate = float(np.clip(genome.mutation_genes[0], *_MUTATION_RATE_BOUNDS))
        sigma = float(np.clip(genome.mutation_genes[1], *_MUTATION_SIGMA_BOUNDS))

        new_mutation_genes = np.clip(
            _mutate_vector(genome.mutation_genes, rate=1.0, sigma=_META_MUTATION_SIGMA, rng=rng),
            [_MUTATION_RATE_BOUNDS[0], _MUTATION_SIGMA_BOUNDS[0]],
            [_MUTATION_RATE_BOUNDS[1], _MUTATION_SIGMA_BOUNDS[1]],
        ).astype(np.float32)

        return Genome(
            architecture=genome.architecture,
            controller_weights=_mutate_vector(genome.controller_weights, rate, sigma, rng),
            metabolic_genes=_mutate_vector(genome.metabolic_genes, rate, sigma * 0.1, rng),
            mutation_genes=new_mutation_genes,
            learning_genes=_mutate_vector(genome.learning_genes, rate, sigma * 0.1, rng),
        )


def _mutate_vector(
    vector: FloatArray, rate: float, sigma: float, rng: np.random.Generator
) -> FloatArray:
    mutate_mask = rng.random(vector.shape) < rate
    noise = rng.normal(0.0, sigma, vector.shape).astype(vector.dtype)
    result: FloatArray = np.where(mutate_mask, vector + noise, vector).astype(vector.dtype)
    return result
