"""`Individual` (a genome plus population-level identity) and `Population`
(the set of individuals alive in the current generation).

`Population` only manages identity, genomes, and generation/parentage
bookkeeping — it does not run lifetimes, compute fitness, or select
parents; that orchestration is `genevra.evolution.engine.EvolutionEngine`'s
job, kept separate so population bookkeeping doesn't get coupled to one
particular evolutionary loop.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from genevra.organism.genome import ControllerArchitecture, Genome
from genevra.organism.organism import OrganismConfig
from genevra.simulation.types import Action


@dataclass(frozen=True, eq=False)
class Individual:
    id: int
    genome: Genome
    generation: int
    parent_ids: tuple[int, ...]


@dataclass(frozen=True)
class PopulationConfig:
    size: int
    architecture: ControllerArchitecture
    organism_config: OrganismConfig
    initial_mutation_rate: float = 0.1
    initial_mutation_sigma: float = 0.1

    def __post_init__(self) -> None:
        if self.size <= 0:
            raise ValueError("population size must be positive")
        if self.architecture.output_size != len(Action):
            raise ValueError(
                f"architecture.output_size ({self.architecture.output_size}) must equal "
                f"the action space size ({len(Action)})"
            )
        if not 0.0 <= self.initial_mutation_rate <= 1.0:
            raise ValueError("initial_mutation_rate must be in [0, 1]")
        if self.initial_mutation_sigma <= 0:
            raise ValueError("initial_mutation_sigma must be > 0")


class Population:
    def __init__(self, config: PopulationConfig) -> None:
        self._config = config
        self.individuals: list[Individual] = []
        self._next_id = 0

    def initialize(self, rng: np.random.Generator) -> None:
        self.individuals = [self._new_founder(rng) for _ in range(self._config.size)]

    def new_offspring(
        self, genome: Genome, generation: int, parent_ids: tuple[int, ...]
    ) -> Individual:
        return Individual(
            id=self._allocate_id(), genome=genome, generation=generation, parent_ids=parent_ids
        )

    def snapshot_genomes(self) -> list[Genome]:
        return [individual.genome for individual in self.individuals]

    @property
    def size(self) -> int:
        return len(self.individuals)

    def _new_founder(self, rng: np.random.Generator) -> Individual:
        genome = Genome.random(self._config.architecture, rng)
        genome.mutation_genes[:] = [
            self._config.initial_mutation_rate,
            self._config.initial_mutation_sigma,
        ]
        return Individual(id=self._allocate_id(), genome=genome, generation=0, parent_ids=())

    def _allocate_id(self) -> int:
        allocated = self._next_id
        self._next_id += 1
        return allocated
