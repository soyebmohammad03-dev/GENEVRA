"""Novelty: distance from a reference archive of past behavior — not
fitness under another name.

`NoveltyArchive` holds behavioral signatures (`genevra.metrics.behavior`),
never fitness values or genomes, and `score()` is purely a function of
distance to archived behavior. An organism can score high on fitness and
low on novelty (doing the same successful thing as everyone else) or the
reverse (doing something unusual and unrewarded) — see
`tests/test_novelty.py` for a case constructed to demonstrate this.

The reference set is conceptually swappable — this implementation is one
concrete choice (a size-capped, randomly-evicting historical archive, in
the spirit of novelty search's persistent archive of past behavior).
Building the same interface around "current population" or "per-lineage"
reference sets instead is future work; nothing here assumes an archive is
the only possible reference set.
"""

from __future__ import annotations

import numpy as np

from genevra.arrays import FloatArray
from genevra.metrics.diversity import DistanceMetric


class NoveltyArchive:
    def __init__(self, max_size: int, rng: np.random.Generator) -> None:
        if max_size <= 0:
            raise ValueError("max_size must be positive")
        self._max_size = max_size
        self._rng = rng
        self._signatures: list[FloatArray] = []

    def add(self, signature: FloatArray) -> None:
        if len(self._signatures) < self._max_size:
            self._signatures.append(signature)
        else:
            # ponytail: random eviction, not "evict least novel" — a
            # smarter retention policy is future work, not a permanent
            # ceiling on this class.
            index = int(self._rng.integers(0, self._max_size))
            self._signatures[index] = signature

    def score(self, signature: FloatArray, distance: DistanceMetric, k: int = 5) -> float:
        """Mean distance to the k nearest archive neighbors (Lehman &
        Stanley-style novelty). 0.0 for an empty archive — there is
        nothing to be novel against yet."""
        if not self._signatures:
            return 0.0
        distances = sorted(
            distance.distance(signature, reference) for reference in self._signatures
        )
        neighbors = distances[: min(k, len(distances))]
        return float(np.mean(neighbors))

    def __len__(self) -> int:
        return len(self._signatures)
