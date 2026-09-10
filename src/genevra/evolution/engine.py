"""`EvolutionEngine`: the explicit, staged generational loop.

One `step()` call is one discrete generation, broken into named stages
(run lifetimes -> compute fitness -> determine reproduction eligibility ->
select parents -> reproduce -> record) rather than one undifferentiated
function, so each stage can be read, tested, and later replaced (e.g. an
overlapping-generations loop, a different reproduction eligibility rule)
independently. See `docs/architecture.md` for how this maps onto the
conceptual 15-step evolutionary lifecycle.
"""

from __future__ import annotations

import time
from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum

import numpy as np

from genevra.evolution.fitness import FitnessFunction
from genevra.evolution.lifetime import LifetimeRecord, run_single_lifetime
from genevra.evolution.lineage import LineageTracker
from genevra.evolution.population import Individual, Population, PopulationConfig
from genevra.evolution.reproduction import PopulationReproduction, PopulationReproductionConfig
from genevra.evolution.selection import SelectionStrategy
from genevra.metrics.behavior import behavioral_signature
from genevra.metrics.distribution import summarize_distribution
from genevra.metrics.diversity import EuclideanDistance, behavioral_diversity, genotypic_diversity
from genevra.metrics.fitness_metrics import FitnessSummary, compute_fitness_summary
from genevra.metrics.novelty import NoveltyArchive
from genevra.metrics.trajectory import GenerationSnapshot, MetricsLevel, Trajectory
from genevra.organism.genome import Genome
from genevra.organism.learning import LearningRule, NoLearning
from genevra.simulation.grid_world import GridWorldConfig


class RunStatus(Enum):
    NOT_STARTED = "not_started"
    RUNNING = "running"
    COMPLETED = "completed"
    EXTINCT = "extinct"
    BUDGET_EXCEEDED = "budget_exceeded"


@dataclass(frozen=True)
class EvolutionConfig:
    generations: int
    steps_per_lifetime: int
    environment_config: GridWorldConfig
    population_config: PopulationConfig
    fitness_function: FitnessFunction
    selection_strategy: SelectionStrategy
    reproduction: PopulationReproductionConfig
    seed: int
    learning_rule_factory: Callable[[], LearningRule] = NoLearning
    novelty_archive_size: int = 200
    metrics_level: MetricsLevel = MetricsLevel.STANDARD
    metrics_interval: int = 1
    """How often (every N generations) `RESEARCH`-level extras are
    computed; ignored at `MINIMAL`/`STANDARD`. Must be >= 1."""
    diversity_max_pairs: int | None = None
    """Caps the number of genome/behavior pairs
    `genotypic_diversity`/`behavioral_diversity` sample per generation
    (see `genevra.metrics.diversity.mean_pairwise_distance`) — without
    this, both are O(population_size^2) every generation. `None`
    preserves exact (uncapped) computation."""
    max_runtime_seconds: float | None = None
    """An explicit wall-clock budget (Phase 7.6): if set, `run()` stops
    before starting a generation that would exceed it, sets
    `status=BUDGET_EXCEEDED` and records why in `budget_exceeded_reason`
    — never silently truncates a run and reports it as `COMPLETED`."""
    eval_environment_config: GridWorldConfig | None = None
    """A held-out environment (Phase 8.4): when set, every generation's
    survivors are additionally evaluated here (never selected on) and
    the result recorded separately as
    `GenerationSnapshot.eval_fitness_summary`."""

    def __post_init__(self) -> None:
        if self.generations <= 0:
            raise ValueError("generations must be positive")
        if self.steps_per_lifetime <= 0:
            raise ValueError("steps_per_lifetime must be positive")
        if self.novelty_archive_size <= 0:
            raise ValueError("novelty_archive_size must be positive")
        if self.metrics_interval < 1:
            raise ValueError("metrics_interval must be >= 1")
        if self.diversity_max_pairs is not None and self.diversity_max_pairs <= 0:
            raise ValueError("diversity_max_pairs must be positive")
        if self.max_runtime_seconds is not None and self.max_runtime_seconds <= 0:
            raise ValueError("max_runtime_seconds must be positive")


class EvolutionEngine:
    def __init__(self, config: EvolutionConfig) -> None:
        self._config = config
        self._rng = np.random.default_rng(config.seed)
        self.population = Population(config.population_config)
        self.lineage = LineageTracker()
        self.reproduction = PopulationReproduction(config.reproduction)
        self.trajectory = Trajectory()
        self.generation = 0
        self.status = RunStatus.NOT_STARTED
        self.budget_exceeded_reason: str | None = None

        self._novelty_archive = NoveltyArchive(max_size=config.novelty_archive_size, rng=self._rng)
        self._novelty_distance = EuclideanDistance()
        self._previous_genome_centroid: np.ndarray | None = None
        self._previous_behavior_centroid: np.ndarray | None = None
        self._start_time: float | None = None

    def initialize(self) -> None:
        self.population.initialize(self._rng)
        for individual in self.population.individuals:
            self.lineage.record_birth(
                individual.id, individual.parent_ids, individual.generation, individual.genome
            )
        self.status = RunStatus.RUNNING
        self._start_time = time.monotonic()

    def run(self) -> Trajectory:
        self.initialize()
        for _ in range(self._config.generations):
            if self.status != RunStatus.RUNNING:
                break
            if self._runtime_budget_exceeded():
                self.status = RunStatus.BUDGET_EXCEEDED
                self.budget_exceeded_reason = (
                    f"max_runtime_seconds={self._config.max_runtime_seconds} exceeded "
                    f"before generation {self.generation}"
                )
                break
            self.step()
        if self.status == RunStatus.RUNNING:
            self.status = RunStatus.COMPLETED
        return self.trajectory

    def _runtime_budget_exceeded(self) -> bool:
        budget = self._config.max_runtime_seconds
        if budget is None or self._start_time is None:
            return False
        return (time.monotonic() - self._start_time) > budget

    def step(self) -> GenerationSnapshot:
        records = self._run_lifetimes()
        fitness_scores = self._compute_fitness(records)
        final_energies = [record.observations.final_energy for record in records]
        eligible_indices = self.reproduction.eligible_parent_indices(final_energies)
        extinction = len(eligible_indices) == 0

        for individual in self.population.individuals:
            self.lineage.record_death(individual.id, self.generation)

        selected_indices = self._select_parents(fitness_scores, eligible_indices, extinction)
        eval_fitness_summary = (
            self._evaluate_generalization(self.population.snapshot_genomes())
            if self._config.eval_environment_config is not None
            else None
        )
        snapshot = self._build_snapshot(
            records, fitness_scores, selected_indices, extinction, eval_fitness_summary
        )
        self.trajectory.append(snapshot)

        if extinction:
            self.status = RunStatus.EXTINCT
            self.population.individuals = []
            self.generation += 1
            return snapshot

        self.population.individuals = self._reproduce(selected_indices)
        self.generation += 1
        return snapshot

    def _run_lifetimes(self) -> list[LifetimeRecord]:
        records = []
        for individual in self.population.individuals:
            env_seed = int(self._rng.integers(0, 2**31 - 1))
            organism_seed = int(self._rng.integers(0, 2**31 - 1))
            observations = run_single_lifetime(
                genome=individual.genome,
                environment_config=self._config.environment_config,
                organism_config=self._config.population_config.organism_config,
                learning_rule=self._config.learning_rule_factory(),
                env_seed=env_seed,
                organism_seed=organism_seed,
                max_steps=self._config.steps_per_lifetime,
            )
            records.append(LifetimeRecord(individual_id=individual.id, observations=observations))
        return records

    def _compute_fitness(self, records: list[LifetimeRecord]) -> list[float]:
        return [self._config.fitness_function.compute(record.observations) for record in records]

    def _evaluate_generalization(self, genomes: list[Genome]) -> FitnessSummary:
        """Phase 8.4: fitness on a held-out `eval_environment_config`,
        run for every current genome but never fed into
        `eligible_indices`/selection — this population never evolves on
        this environment, it is only measured on it."""
        eval_config = self._config.eval_environment_config
        assert eval_config is not None
        scores = []
        for genome in genomes:
            env_seed = int(self._rng.integers(0, 2**31 - 1))
            organism_seed = int(self._rng.integers(0, 2**31 - 1))
            observations = run_single_lifetime(
                genome=genome,
                environment_config=eval_config,
                organism_config=self._config.population_config.organism_config,
                learning_rule=self._config.learning_rule_factory(),
                env_seed=env_seed,
                organism_seed=organism_seed,
                max_steps=self._config.steps_per_lifetime,
            )
            scores.append(self._config.fitness_function.compute(observations))
        return compute_fitness_summary(scores)

    def _select_parents(
        self, fitness_scores: list[float], eligible_indices: list[int], extinction: bool
    ) -> list[int]:
        if extinction:
            return []
        eligible_fitness = [fitness_scores[i] for i in eligible_indices]
        selected_local = self._config.selection_strategy.select(
            eligible_fitness, self._config.population_config.size, self._rng
        )
        return [eligible_indices[i] for i in selected_local]

    def _reproduce(self, selected_indices: list[int]) -> list[Individual]:
        next_generation = self.generation + 1
        next_individuals: list[Individual] = []
        for index in selected_indices:
            parent = self.population.individuals[index]
            self.lineage.record_reproduction(parent.id)
            offspring_genome = self.reproduction.produce_offspring_genome(parent.genome, self._rng)
            offspring = self.population.new_offspring(
                offspring_genome, next_generation, (parent.id,)
            )
            self.lineage.record_birth(
                offspring.id, offspring.parent_ids, offspring.generation, offspring.genome
            )
            next_individuals.append(offspring)
        return next_individuals

    def _build_snapshot(
        self,
        records: list[LifetimeRecord],
        fitness_scores: list[float],
        selected_indices: list[int],
        extinction: bool,
        eval_fitness_summary: FitnessSummary | None,
    ) -> GenerationSnapshot:
        level = self._config.metrics_level
        fitness_summary = compute_fitness_summary(fitness_scores)
        genomes = self.population.snapshot_genomes()

        survival_rate = (
            float(np.mean([r.observations.survived_full_lifetime for r in records]))
            if records
            else 0.0
        )
        reproductive_success_rate = (
            len({records[i].individual_id for i in selected_indices}) / len(records)
            if records
            else 0.0
        )
        mutation_rates = [float(g.mutation_genes[0]) for g in genomes]
        mutation_sigmas = [float(g.mutation_genes[1]) for g in genomes]
        mean_mutation_rate = float(np.mean(mutation_rates)) if mutation_rates else 0.0
        mean_mutation_sigma = float(np.mean(mutation_sigmas)) if mutation_sigmas else 0.0

        if level is MetricsLevel.MINIMAL:
            return GenerationSnapshot(
                generation=self.generation,
                fitness_summary=fitness_summary,
                genotypic_diversity=0.0,
                behavioral_diversity=0.0,
                mean_novelty=0.0,
                instantaneous_novelty=0.0,
                survival_rate=survival_rate,
                reproductive_success_rate=reproductive_success_rate,
                mean_mutation_rate=mean_mutation_rate,
                mean_mutation_sigma=mean_mutation_sigma,
                genome_centroid_shift=None,
                behavior_centroid_shift=None,
                extinction=extinction,
                eval_fitness_summary=eval_fitness_summary,
                metrics_level=level.value,
            )

        max_pairs = self._config.diversity_max_pairs
        signatures = [behavioral_signature(record.observations) for record in records]

        novelty_scores = [
            self._novelty_archive.score(sig, self._novelty_distance) for sig in signatures
        ]
        instantaneous_novelty = _leave_one_out_novelty(signatures, self._novelty_distance)
        for sig in signatures:
            self._novelty_archive.add(sig)
        mean_novelty = float(np.mean(novelty_scores)) if novelty_scores else 0.0

        genome_centroid = (
            np.mean([g.controller_weights for g in genomes], axis=0) if genomes else None
        )
        behavior_centroid = np.mean(signatures, axis=0) if signatures else None
        genome_shift = _centroid_shift(genome_centroid, self._previous_genome_centroid)
        behavior_shift = _centroid_shift(behavior_centroid, self._previous_behavior_centroid)
        self._previous_genome_centroid = genome_centroid
        self._previous_behavior_centroid = behavior_centroid

        learning_gene_stats = None
        if level is MetricsLevel.RESEARCH and self.generation % self._config.metrics_interval == 0:
            learning_gene_stats = (
                tuple(
                    summarize_distribution([float(g.learning_genes[i]) for g in genomes])
                    for i in range(genomes[0].learning_genes.shape[0])
                )
                if genomes
                else ()
            )

        return GenerationSnapshot(
            generation=self.generation,
            fitness_summary=fitness_summary,
            genotypic_diversity=genotypic_diversity(genomes, max_pairs=max_pairs, rng=self._rng),
            behavioral_diversity=behavioral_diversity(
                signatures, max_pairs=max_pairs, rng=self._rng
            ),
            mean_novelty=mean_novelty,
            instantaneous_novelty=instantaneous_novelty,
            survival_rate=survival_rate,
            reproductive_success_rate=reproductive_success_rate,
            mean_mutation_rate=mean_mutation_rate,
            mean_mutation_sigma=mean_mutation_sigma,
            genome_centroid_shift=genome_shift,
            behavior_centroid_shift=behavior_shift,
            extinction=extinction,
            learning_gene_stats=learning_gene_stats,
            eval_fitness_summary=eval_fitness_summary,
            metrics_level=level.value,
        )


def _centroid_shift(current: np.ndarray | None, previous: np.ndarray | None) -> float | None:
    if current is None or previous is None:
        return None
    return float(np.linalg.norm(current - previous))


def _leave_one_out_novelty(
    signatures: list[np.ndarray], distance: EuclideanDistance, k: int = 5
) -> float:
    """Instantaneous novelty: score each signature by its mean distance to
    the k nearest *other* signatures in this same generation, ignoring all
    history (contrast `NoveltyArchive`-based `mean_novelty`, which is
    cumulative across generations). O(n^2) in population size — fine at
    the population sizes GENEVRA targets; a cost to revisit if population
    sizes grow much larger."""
    if len(signatures) < 2:
        return 0.0
    scores = []
    for i, signature in enumerate(signatures):
        others = signatures[:i] + signatures[i + 1 :]
        distances = sorted(distance.distance(signature, other) for other in others)
        scores.append(float(np.mean(distances[: min(k, len(distances))])))
    return float(np.mean(scores))
