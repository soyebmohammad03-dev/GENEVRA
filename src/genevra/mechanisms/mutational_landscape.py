"""Phase 13.7: mutational-neighborhood characterization, extending
`genevra.metrics.evolvability.EvolvabilityAnalyzer` (which reports a
summary) with the underlying per-mutant distribution plus an explicitly
labeled, small, *sampled* (never exhaustive) two-step neighborhood.

Sample sizes are small by default and always reported on the result —
Phase 13.7's "do not attempt millions of mutants on a laptop" and
"clearly distinguish exact enumeration from stochastic sampling"
requirements.
"""

from __future__ import annotations

import dataclasses
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

import numpy as np

from genevra.arrays import FloatArray
from genevra.metrics.diversity import DistanceMetric
from genevra.organism.genome import Genome
from genevra.organism.mutation import MutationOperator

_LIMITATION_NOTE = (
    "one_step is a full sample of size num_samples around the given genotype; "
    "two_step (when requested) draws num_two_step_samples independent two-mutation "
    "chains — a small stochastic sample of a neighborhood exponentially larger than "
    "what is enumerated here, not an exhaustive two-step search."
)


@dataclass(frozen=True)
class NeighborhoodSample:
    step: int
    """1 for one-step mutants, 2 for two-step chains."""
    n_samples: int
    neutral_fraction: float | None
    deleterious_fraction: float | None
    beneficial_fraction: float | None
    viable_fraction: float
    behavioral_distances: tuple[float, ...]
    fitness_deltas: tuple[float, ...]

    def to_dict(self) -> dict[str, Any]:
        return dataclasses.asdict(self)


@dataclass(frozen=True)
class MutationalLandscapeReport:
    one_step: NeighborhoodSample
    two_step: NeighborhoodSample | None
    limitation_note: str = field(default=_LIMITATION_NOTE)

    def to_dict(self) -> dict[str, Any]:
        return {
            "one_step": self.one_step.to_dict(),
            "two_step": self.two_step.to_dict() if self.two_step else None,
            "limitation_note": self.limitation_note,
        }


class MutationalLandscapeAnalyzer:
    """`behavioral_evaluator`/`fitness_evaluator` follow the same
    injected-callback shape as `EvolvabilityAnalyzer` — no second
    lifetime-execution path is introduced here."""

    def __init__(
        self,
        mutation_operator: MutationOperator,
        behavioral_evaluator: Callable[[Genome], FloatArray],
        distance: DistanceMetric,
        fitness_evaluator: Callable[[Genome], float] | None = None,
        neutral_fitness_epsilon: float = 1e-6,
    ) -> None:
        self._mutation_operator = mutation_operator
        self._behavioral_evaluator = behavioral_evaluator
        self._distance = distance
        self._fitness_evaluator = fitness_evaluator
        self._neutral_fitness_epsilon = neutral_fitness_epsilon

    def _sample_one_step(
        self,
        genomes: list[Genome],
        baseline_signature: FloatArray,
        baseline_fitness: float | None,
        rng: np.random.Generator,
        num_samples: int,
        step: int = 1,
    ) -> tuple[list[Genome], NeighborhoodSample]:
        mutants: list[Genome] = []
        distances: list[float] = []
        fitness_deltas: list[float] = []
        num_viable = 0
        for genome in genomes:
            for _ in range(num_samples):
                mutant = self._mutation_operator.mutate(genome, rng)
                try:
                    signature = self._behavioral_evaluator(mutant)
                except Exception:
                    continue
                num_viable += 1
                mutants.append(mutant)
                distances.append(self._distance.distance(signature, baseline_signature))
                if self._fitness_evaluator is not None and baseline_fitness is not None:
                    fitness_deltas.append(self._fitness_evaluator(mutant) - baseline_fitness)

        total_samples = len(genomes) * num_samples
        neutral = deleterious = beneficial = None
        if fitness_deltas:
            eps = self._neutral_fitness_epsilon
            deltas = np.asarray(fitness_deltas)
            beneficial = float(np.mean(deltas > eps))
            deleterious = float(np.mean(deltas < -eps))
            neutral = float(np.mean(np.abs(deltas) <= eps))

        sample = NeighborhoodSample(
            step=step,
            n_samples=total_samples,
            neutral_fraction=neutral,
            deleterious_fraction=deleterious,
            beneficial_fraction=beneficial,
            viable_fraction=num_viable / total_samples if total_samples else 0.0,
            behavioral_distances=tuple(distances),
            fitness_deltas=tuple(fitness_deltas),
        )
        return mutants, sample

    def analyze(
        self,
        genome: Genome,
        rng: np.random.Generator,
        num_samples: int = 12,
        include_two_step: bool = False,
        num_two_step_samples: int = 6,
    ) -> MutationalLandscapeReport:
        if num_samples <= 0:
            raise ValueError("num_samples must be positive")
        baseline_signature = self._behavioral_evaluator(genome)
        baseline_fitness = (
            self._fitness_evaluator(genome) if self._fitness_evaluator is not None else None
        )
        one_step_mutants, one_step = self._sample_one_step(
            [genome], baseline_signature, baseline_fitness, rng, num_samples
        )

        two_step: NeighborhoodSample | None = None
        if include_two_step:
            if num_two_step_samples <= 0:
                raise ValueError("num_two_step_samples must be positive")
            if one_step_mutants:
                chosen = [
                    one_step_mutants[int(rng.integers(0, len(one_step_mutants)))]
                    for _ in range(num_two_step_samples)
                ]
                _, two_step = self._sample_one_step(
                    chosen, baseline_signature, baseline_fitness, rng, 1, step=2
                )
            else:
                two_step = NeighborhoodSample(
                    step=2,
                    n_samples=0,
                    neutral_fraction=None,
                    deleterious_fraction=None,
                    beneficial_fraction=None,
                    viable_fraction=0.0,
                    behavioral_distances=(),
                    fitness_deltas=(),
                )

        return MutationalLandscapeReport(one_step=one_step, two_step=two_step)


__all__ = ["NeighborhoodSample", "MutationalLandscapeReport", "MutationalLandscapeAnalyzer"]
