"""Population-level (between-generation) reproduction.

This is the discrete-generation batch analog of
`genevra.organism.reproduction.ReproductionSystem`, which models a single
still-living organism deciding, during its own lifetime, whether it has
enough energy to reproduce — a hook meant for a future overlapping-
generations or continuous-time model. Here, every individual's lifetime
has already ended for the generation; `PopulationReproduction` only
determines which of those now-finished lifetimes were successful enough to
found the next generation, and generates one mutated offspring genome per
selection draw.

Kept separate from `SelectionStrategy` (which only ranks/chooses *among*
eligible individuals) and from `MutationOperator` (which only perturbs a
genome) — this class composes them plus an eligibility rule, and nothing
else, so recombination/crossover can be added later as an alternative
offspring-generation step without touching eligibility or selection.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

import numpy as np

from genevra.organism.genome import Genome
from genevra.organism.mutation import MutationOperator


@dataclass(frozen=True)
class PopulationReproductionConfig:
    """`energy_threshold` may be negative: it is only a cutoff compared
    against an organism's final energy, not itself an energy value that
    must be physically meaningful. A very negative threshold is a
    reasonable way to make (almost) every individual reproduction-eligible
    in a test or experiment, without disabling the eligibility rule."""

    energy_threshold: float
    mutation_operator: MutationOperator


class PopulationReproduction:
    def __init__(self, config: PopulationReproductionConfig) -> None:
        self._config = config

    def eligible_parent_indices(self, final_energies: Sequence[float]) -> list[int]:
        threshold = self._config.energy_threshold
        return [index for index, energy in enumerate(final_energies) if energy >= threshold]

    def produce_offspring_genome(self, parent_genome: Genome, rng: np.random.Generator) -> Genome:
        """Mutates a *copy* of the parent genome — `MutationOperator`
        implementations allocate new arrays, so `parent_genome` is never
        modified (see `tests/test_population_reproduction.py`)."""
        return self._config.mutation_operator.mutate(parent_genome, rng)
