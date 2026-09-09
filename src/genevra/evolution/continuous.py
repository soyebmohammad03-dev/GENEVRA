"""An overlapping-generations evolutionary engine, coexisting with the
discrete-generation `EvolutionEngine` (`genevra.evolution.engine`) rather
than replacing it.

Where `EvolutionEngine` runs whole non-overlapping generations (every
individual's lifetime starts and ends together), `ContinuousEvolutionEngine`
runs one shared `SharedGridWorld` across many timesteps: individuals of
different ages coexist, act every timestep, can die at any time (energy
reaching zero), and can reproduce into the same running world whenever
they are eligible and there is population capacity. This is a first,
deliberately simple overlapping-generations model — not fully asynchronous
or event-driven — but it is the minimum needed to make "organism age" and
"population with mixed generations" real, queryable properties instead of
concepts that only exist between discrete generations.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field

import numpy as np

from genevra.evolution.lineage import LineageTracker
from genevra.organism.genome import ControllerArchitecture, Genome
from genevra.organism.learning import LearningRule, NoLearning
from genevra.organism.mutation import GaussianMutation, MutationOperator
from genevra.organism.organism import Organism, OrganismConfig
from genevra.simulation.shared_grid_world import SharedGridWorld, SharedGridWorldConfig
from genevra.simulation.types import Action


@dataclass(eq=False)
class LivingOrganism:
    """One individual currently alive in a `ContinuousEvolutionEngine`
    run: identity/ancestry plus the live `Organism` instance carrying its
    lifetime state (memory, learning state, metabolism)."""

    id: int
    genome: Genome
    organism: Organism
    birth_step: int
    parent_ids: tuple[int, ...]

    def age_at(self, step: int) -> int:
        return step - self.birth_step


@dataclass(frozen=True)
class EcologicalSnapshot:
    """Compact population statistics recorded every `log_every` steps —
    not every step, so history stays bounded regardless of run length."""

    step: int
    population_size: int
    mean_age: float
    age_std: float
    mean_energy: float
    births_since_last_snapshot: int
    deaths_since_last_snapshot: int
    resource_consumed_since_last_snapshot: float
    interaction_events_since_last_snapshot: int


@dataclass(frozen=True)
class ContinuousEvolutionConfig:
    total_steps: int
    initial_population: int
    max_population: int
    environment_config: SharedGridWorldConfig
    architecture: ControllerArchitecture
    organism_config: OrganismConfig
    reproduction_energy_threshold: float
    offspring_energy_cost: float
    seed: int
    initial_mutation_rate: float = 0.1
    initial_mutation_sigma: float = 0.1
    mutation_operator: MutationOperator = field(default_factory=GaussianMutation)
    learning_rule_factory: Callable[[], LearningRule] = NoLearning
    log_every: int = 10

    def __post_init__(self) -> None:
        if self.total_steps <= 0:
            raise ValueError("total_steps must be positive")
        if self.initial_population <= 0:
            raise ValueError("initial_population must be positive")
        if self.max_population < self.initial_population:
            raise ValueError("max_population must be >= initial_population")
        if self.architecture.output_size != len(Action):
            raise ValueError("architecture.output_size must equal the action space size")
        if self.log_every <= 0:
            raise ValueError("log_every must be positive")


class ContinuousEvolutionEngine:
    def __init__(self, config: ContinuousEvolutionConfig) -> None:
        self._config = config
        self._rng = np.random.default_rng(config.seed)
        self._environment = SharedGridWorld(config.environment_config)
        self._environment.reset(seed=int(self._rng.integers(0, 2**31 - 1)))
        self.population: dict[int, LivingOrganism] = {}
        self.lineage = LineageTracker()
        self.history: list[EcologicalSnapshot] = []
        self.step_index = 0
        self._next_id = 0

        self._births_since_snapshot = 0
        self._deaths_since_snapshot = 0
        self._resource_since_snapshot = 0.0
        self._interactions_since_snapshot = 0

    def initialize(self) -> None:
        for _ in range(self._config.initial_population):
            self._spawn(genome=None, parent_ids=())

    def run(self) -> list[EcologicalSnapshot]:
        self.initialize()
        for _ in range(self._config.total_steps):
            self._tick()
        return self.history

    def _tick(self) -> None:
        observations = {oid: self._environment.observe(oid) for oid in self.population}
        actions = {
            oid: living.organism.act(observations[oid]) for oid, living in self.population.items()
        }

        previous_interaction_events = self._environment.interaction_events
        results = self._environment.step(actions)
        self._interactions_since_snapshot += (
            self._environment.interaction_events - previous_interaction_events
        )

        dead_ids: list[int] = []
        for oid, result in results.items():
            living = self.population[oid]
            living.organism.learn_from_feedback(actions[oid], result.reward)
            self._resource_since_snapshot += result.reward
            if not living.organism.is_alive:
                dead_ids.append(oid)

        for oid in dead_ids:
            self._environment.remove_agent(oid)
            self.lineage.record_death(oid, self.step_index)
            del self.population[oid]
            self._deaths_since_snapshot += 1

        self._maybe_reproduce()

        if self.step_index % self._config.log_every == 0:
            self._record_snapshot()

        self.step_index += 1

    def _maybe_reproduce(self) -> None:
        if len(self.population) >= self._config.max_population:
            return
        eligible = [
            oid
            for oid, living in self.population.items()
            if living.organism.metabolism.energy >= self._config.reproduction_energy_threshold
        ]
        if not eligible:
            return
        parent_id = int(self._rng.choice(eligible))
        parent = self.population[parent_id]
        offspring_genome = self._config.mutation_operator.mutate(parent.genome, self._rng)
        parent.organism.metabolism.energy -= self._config.offspring_energy_cost
        self.lineage.record_reproduction(parent_id)
        self._spawn(genome=offspring_genome, parent_ids=(parent_id,))
        self._births_since_snapshot += 1

    def _spawn(self, genome: Genome | None, parent_ids: tuple[int, ...]) -> None:
        cfg = self._config
        if genome is None:
            genome = Genome.random(cfg.architecture, self._rng)
            genome.mutation_genes[:] = [cfg.initial_mutation_rate, cfg.initial_mutation_sigma]
        agent_id = self._allocate_id()
        organism = Organism(
            genome,
            cfg.organism_config,
            cfg.learning_rule_factory(),
            np.random.default_rng(int(self._rng.integers(0, 2**31 - 1))),
        )
        self._environment.add_agent(agent_id)
        self.population[agent_id] = LivingOrganism(
            id=agent_id,
            genome=genome,
            organism=organism,
            birth_step=self.step_index,
            parent_ids=parent_ids,
        )
        self.lineage.record_birth(agent_id, parent_ids, generation=self.step_index, genome=genome)

    def _record_snapshot(self) -> None:
        ages = [living.age_at(self.step_index) for living in self.population.values()]
        energies = [living.organism.metabolism.energy for living in self.population.values()]
        self.history.append(
            EcologicalSnapshot(
                step=self.step_index,
                population_size=len(self.population),
                mean_age=float(np.mean(ages)) if ages else 0.0,
                age_std=float(np.std(ages)) if ages else 0.0,
                mean_energy=float(np.mean(energies)) if energies else 0.0,
                births_since_last_snapshot=self._births_since_snapshot,
                deaths_since_last_snapshot=self._deaths_since_snapshot,
                resource_consumed_since_last_snapshot=self._resource_since_snapshot,
                interaction_events_since_last_snapshot=self._interactions_since_snapshot,
            )
        )
        self._births_since_snapshot = 0
        self._deaths_since_snapshot = 0
        self._resource_since_snapshot = 0.0
        self._interactions_since_snapshot = 0

    def _allocate_id(self) -> int:
        allocated = self._next_id
        self._next_id += 1
        return allocated
