"""Genotypic and behavioral diversity, kept as separate measurements over
a shared distance abstraction.

Genotypic diversity is distance between genome parameter vectors
(`controller_weights`). Behavioral diversity is distance between
behavioral signatures (`genevra.metrics.behavior.behavioral_signature`) —
derived from what organisms actually did, not from their genomes. Calling
genome-vector distance "behavioral diversity" would conflate two
scientifically distinct quantities; this module never does that.
"""

from __future__ import annotations

import itertools
from collections.abc import Sequence
from typing import Protocol

import numpy as np

from genevra.arrays import FloatArray
from genevra.organism.genome import Genome


class DistanceMetric(Protocol):
    def distance(self, a: FloatArray, b: FloatArray) -> float: ...


class EuclideanDistance:
    def distance(self, a: FloatArray, b: FloatArray) -> float:
        return float(np.linalg.norm(a - b))


class CosineDistance:
    """1 - cosine similarity. Returns the maximal distance (1.0) for a
    zero vector, since cosine similarity is undefined there."""

    def distance(self, a: FloatArray, b: FloatArray) -> float:
        norm_a, norm_b = float(np.linalg.norm(a)), float(np.linalg.norm(b))
        if norm_a == 0.0 or norm_b == 0.0:
            return 1.0
        return float(1.0 - np.dot(a, b) / (norm_a * norm_b))


def mean_pairwise_distance(
    vectors: Sequence[FloatArray],
    distance: DistanceMetric | None = None,
    rng: np.random.Generator | None = None,
    max_pairs: int | None = None,
) -> float:
    """Mean distance over all (or, for large populations, a sampled
    subset of) pairs. Degenerate cases (0 or 1 vectors) return 0.0 —
    there is no diversity to measure among fewer than two individuals."""
    n = len(vectors)
    if n < 2:
        return 0.0
    metric = distance if distance is not None else EuclideanDistance()
    pairs = list(itertools.combinations(range(n), 2))
    if max_pairs is not None and len(pairs) > max_pairs:
        if rng is None:
            raise ValueError("rng is required when subsampling pairs via max_pairs")
        chosen = rng.choice(len(pairs), size=max_pairs, replace=False)
        pairs = [pairs[i] for i in chosen]
    distances = [metric.distance(vectors[i], vectors[j]) for i, j in pairs]
    return float(np.mean(distances))


def genotypic_diversity(
    genomes: Sequence[Genome],
    distance: DistanceMetric | None = None,
    rng: np.random.Generator | None = None,
    max_pairs: int | None = None,
) -> float:
    vectors = [genome.controller_weights for genome in genomes]
    return mean_pairwise_distance(vectors, distance, rng, max_pairs)


def behavioral_diversity(
    signatures: Sequence[FloatArray],
    distance: DistanceMetric | None = None,
    rng: np.random.Generator | None = None,
    max_pairs: int | None = None,
) -> float:
    return mean_pairwise_distance(signatures, distance, rng, max_pairs)
