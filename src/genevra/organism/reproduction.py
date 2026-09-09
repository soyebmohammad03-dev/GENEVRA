"""The reproduction interface for a single organism.

This intentionally stops at "can this organism produce an offspring
genome" — population-level concerns (selection, who reproduces with whom,
population size control) are evolution-engine responsibilities for a later
phase, not this organism's.
"""

from __future__ import annotations

import numpy as np

from genevra.organism.genome import Genome
from genevra.organism.metabolism import Metabolism
from genevra.organism.mutation import MutationOperator


class ReproductionSystem:
    def __init__(
        self,
        mutation_operator: MutationOperator,
        energy_threshold: float,
        offspring_energy_cost: float,
    ) -> None:
        self._mutation_operator = mutation_operator
        self._energy_threshold = energy_threshold
        self._offspring_energy_cost = offspring_energy_cost

    def can_reproduce(self, metabolism: Metabolism) -> bool:
        return metabolism.energy >= self._energy_threshold

    def reproduce(
        self, parent_genome: Genome, parent_metabolism: Metabolism, rng: np.random.Generator
    ) -> Genome:
        if not self.can_reproduce(parent_metabolism):
            raise RuntimeError("organism does not meet the reproduction energy threshold")
        offspring_genome = self._mutation_operator.mutate(parent_genome, rng)
        parent_metabolism.energy -= self._offspring_energy_cost
        return offspring_genome
