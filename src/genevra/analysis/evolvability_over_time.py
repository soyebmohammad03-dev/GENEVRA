"""Sampling `EvolvabilityAnalyzer` at chosen generations of an
`EvolutionEngine` run, so "does evolvability change over evolutionary
time?" becomes a question with actual data behind it — bounded and
configurable, not a per-generation, per-organism sweep.

`sample_evolvability_over_generations` drives the engine itself (calling
`initialize()`/`step()`), inspecting `engine.population` at each requested
generation *before* advancing past it — `EvolutionEngine.step()` already
replaces the population with the next generation by the time it returns,
so genomes must be captured right before that generation's `step()` call.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Protocol

import numpy as np

from genevra.evolution.engine import EvolutionEngine, RunStatus
from genevra.evolution.lineage import LineageTracker
from genevra.metrics.evolvability import EvolvabilityAnalyzer, EvolvabilityReport
from genevra.organism.genome import Genome


class SamplingStrategy(Protocol):
    def select(self, genomes: dict[int, Genome], k: int, rng: np.random.Generator) -> list[int]: ...


class RandomSampling:
    def select(self, genomes: dict[int, Genome], k: int, rng: np.random.Generator) -> list[int]:
        ids = list(genomes)
        size = min(k, len(ids))
        chosen = rng.choice(len(ids), size=size, replace=False)
        return [ids[i] for i in chosen]


class TopScoreSampling:
    """Picks the `k` genomes with the highest value under a caller-
    supplied scoring function — e.g. a quick re-evaluated fitness
    estimate. Not tied to "fitness" specifically: any `Genome -> float`
    score works."""

    def __init__(self, score_fn: Callable[[Genome], float]) -> None:
        self._score_fn = score_fn

    def select(self, genomes: dict[int, Genome], k: int, rng: np.random.Generator) -> list[int]:
        scored = sorted(genomes.items(), key=lambda item: self._score_fn(item[1]), reverse=True)
        return [individual_id for individual_id, _ in scored[:k]]


class LineageSampling:
    """Picks at most one representative per distinct founding lineage
    present in the current population, so sampled genomes come from
    different ancestral lines rather than clustering within one dominant
    lineage."""

    def __init__(self, lineage: LineageTracker) -> None:
        self._lineage = lineage

    def select(self, genomes: dict[int, Genome], k: int, rng: np.random.Generator) -> list[int]:
        representative_by_root: dict[int, int] = {}
        for individual_id in genomes:
            ancestors = self._lineage.ancestors(individual_id)
            root = ancestors[-1] if ancestors else individual_id
            representative_by_root.setdefault(root, individual_id)
        return list(representative_by_root.values())[:k]


@dataclass(frozen=True)
class EvolvabilitySample:
    generation: int
    individual_id: int
    report: EvolvabilityReport


def sample_evolvability_over_generations(
    engine: EvolutionEngine,
    target_generations: set[int],
    strategy: SamplingStrategy,
    analyzer: EvolvabilityAnalyzer,
    samples_per_generation: int,
    rng: np.random.Generator,
) -> list[EvolvabilitySample]:
    if not target_generations:
        return []
    if engine.status == RunStatus.NOT_STARTED:
        engine.initialize()

    results: list[EvolvabilitySample] = []
    max_target = max(target_generations)
    while engine.status == RunStatus.RUNNING and engine.generation <= max_target:
        if engine.generation in target_generations:
            genomes = {
                individual.id: individual.genome for individual in engine.population.individuals
            }
            chosen_ids = strategy.select(genomes, samples_per_generation, rng)
            for individual_id in chosen_ids:
                report = analyzer.analyze(genomes[individual_id], rng)
                results.append(
                    EvolvabilitySample(
                        generation=engine.generation, individual_id=individual_id, report=report
                    )
                )
        engine.step()

    return results
