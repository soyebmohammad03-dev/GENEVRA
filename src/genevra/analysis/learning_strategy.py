"""An explicit, analyzable representation of a *learning strategy* —
distinct from both neural-controller weights and lifetime learning state.

`genevra.organism.learning` already draws the (A) inherited weights /
(B) lifetime-plastic-state / (C) heritable-control-of-learning line (see
its module docstring and `genevra.organism.__init__`). This module adds
nothing to that split — it exposes group (C), as computed by
`genevra.organism.phenotype.develop`, in a form suitable for comparison,
clustering, lineage tracking, and population-level distribution analysis,
kept independent of `genome.controller_weights`.

Only the three learning genes GENEVRA actually implements behavior for
(`learning_rate`, `plasticity_gate`, `decay` — see
`genevra.organism.learning.HebbianLearning`) are represented here.
Additional dimensions (exploration tendency, adaptation threshold,
learning persistence, ...) are deliberately not added until a
corresponding mechanism exists to give them a scientific interpretation.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass

import numpy as np

from genevra.arrays import FloatArray
from genevra.metrics.diversity import DistanceMetric, mean_pairwise_distance
from genevra.organism.genome import Genome
from genevra.organism.phenotype import develop

STRATEGY_DIMENSIONS: tuple[str, ...] = ("learning_rate", "plasticity_gate", "decay")


@dataclass(frozen=True)
class LearningStrategy:
    """The heritable, interpretable control of *how* an organism learns —
    independent of both `controller_weights` (what it starts knowing) and
    `LearningState` (what it has learned so far this lifetime). Two
    organisms can share a `LearningStrategy` while differing arbitrarily
    in controller weights, and vice versa."""

    learning_rate: float
    plasticity_gate: float
    decay: float

    @classmethod
    def from_genome(cls, genome: Genome) -> LearningStrategy:
        """Uses `phenotype.develop` (the one genotype-to-phenotype map),
        not a second reimplementation of gene clipping."""
        params = develop(genome).learning_params
        return cls(
            learning_rate=params.learning_rate,
            plasticity_gate=params.plasticity_gate,
            decay=params.decay,
        )

    def as_vector(self) -> FloatArray:
        vector: FloatArray = np.array(
            [self.learning_rate, self.plasticity_gate, self.decay], dtype=np.float64
        )
        return vector


class WeightedStrategyDistance:
    """A `DistanceMetric` (see `genevra.metrics.diversity`) over
    interpretable `LearningStrategy` dimensions, not raw genome vectors —
    Phase 9.3's requirement that strategy comparison never silently
    degrade into genome Euclidean distance. `weights`, when given, scales
    each dimension's contribution (e.g. to de-emphasize `decay` if its
    scale dominates); defaults to equal weighting."""

    def __init__(self, weights: Mapping[str, float] | None = None) -> None:
        self._weights = np.array(
            [(weights or {}).get(dim, 1.0) for dim in STRATEGY_DIMENSIONS],
            dtype=np.float64,
        )
        if np.any(self._weights < 0):
            raise ValueError("strategy distance weights must be non-negative")

    def distance(self, a: FloatArray, b: FloatArray) -> float:
        diff = (a - b) * self._weights
        return float(np.linalg.norm(diff))

    def strategy_distance(self, a: LearningStrategy, b: LearningStrategy) -> float:
        return self.distance(a.as_vector(), b.as_vector())


def learning_strategy_diversity(
    strategies: Sequence[LearningStrategy],
    distance: WeightedStrategyDistance | None = None,
    rng: np.random.Generator | None = None,
    max_pairs: int | None = None,
) -> float:
    """Mean pairwise `LearningStrategyDistance` across a population
    (Phase 9.4) — reuses `mean_pairwise_distance` rather than
    reimplementing pairwise aggregation, but operates on strategy
    vectors, never genome vectors."""
    metric = distance if distance is not None else WeightedStrategyDistance()
    vectors = [strategy.as_vector() for strategy in strategies]
    return mean_pairwise_distance(vectors, metric, rng, max_pairs)


def strategies_from_genomes(genomes: Sequence[Genome]) -> list[LearningStrategy]:
    return [LearningStrategy.from_genome(g) for g in genomes]


__all__ = [
    "STRATEGY_DIMENSIONS",
    "LearningStrategy",
    "WeightedStrategyDistance",
    "DistanceMetric",
    "learning_strategy_diversity",
    "strategies_from_genomes",
]
