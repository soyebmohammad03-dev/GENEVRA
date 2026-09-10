"""An operational, mutation-neighborhood definition of evolvability.

GENEVRA's long-term research direction includes "can evolvability itself
evolve?" — which requires a measurable, defensible definition of
evolvability, not a property magically stored on a genome. The definition
used here: sample a controlled number of mutations around a genotype,
develop each mutant's phenotype, run each through a short behavioral
evaluation, and measure (a) what fraction of mutants remain viable and
(b) how much the *viable* mutants' behavior differs from the original.

**This is a measurement of mutational variation, not of adaptive success.**
A genotype whose mutational neighborhood produces large, diverse behavioral
changes is not automatically "more evolvable" in the sense of being more
likely to adapt usefully — large undirected variation can just as easily
mean fragility (most variants behave worse, or die) as it can mean latent
adaptive potential. Distinguishing "produces variation" from "produces
*useful* variation" requires selection acting on that variation over
generations, which this analyzer does not perform — it is a single-genotype,
single-step snapshot, run on demand, not a per-generation population
statistic. Treat `EvolvabilityReport` as one input to a larger analysis,
not a conclusion.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field

import numpy as np

from genevra.arrays import FloatArray
from genevra.metrics.diversity import DistanceMetric
from genevra.organism.genome import Genome
from genevra.organism.mutation import MutationOperator

_LIMITATION_NOTE = (
    "Measures mutational variation reachable in one mutation step around this "
    "genotype, not adaptive success: a high mean_behavioral_distance means "
    "mutation produces behaviorally diverse offspring here, not that this "
    "variation is beneficial. Selection over generations, not this analyzer, "
    "determines whether variation is adaptive."
)


@dataclass(frozen=True)
class EvolvabilityReport:
    """`num_viable`/`mean_behavioral_distance` are the original mutation-
    variation measurements (viability + how much *behavior* changed).
    `beneficial_fraction`/`neutral_fraction`/`deleterious_fraction` and
    `fitness_distance_std` (Phase 8.6) are populated only when the
    caller supplies a `fitness_evaluator` to `EvolvabilityAnalyzer` — a
    genuinely separate measurement of whether the fitness-relevant
    *consequence* of a viable mutant is better, indistinguishable from,
    or worse than the baseline, classified against
    `EvolvabilityAnalyzer`'s `neutral_fitness_epsilon`. A mutation that
    produces large behavioral change (high `mean_behavioral_distance`)
    is not automatically beneficial — that is exactly why these two
    measurements are kept as separate fields rather than combined."""

    num_samples: int
    num_viable: int
    mean_behavioral_distance: float
    behavioral_distance_std: float
    viable_fraction: float
    fitness_distance_std: float | None = None
    beneficial_fraction: float | None = None
    neutral_fraction: float | None = None
    deleterious_fraction: float | None = None
    limitation_note: str = field(default=_LIMITATION_NOTE)


class EvolvabilityAnalyzer:
    """Runs the mutation-neighborhood analysis described in this module's
    docstring. `behavioral_evaluator` is an injected `Genome -> FloatArray`
    callback (typically: develop the genome, run one short lifetime via
    `genevra.evolution.lifetime.run_single_lifetime`, and summarize it with
    `genevra.metrics.behavior.behavioral_signature`) so this class has no
    direct dependency on the simulation loop, and callers control the
    computational budget both via `num_samples` here and via how short they
    make the evaluator's lifetime.

    `num_samples` defaults small deliberately — this analysis is meant to
    be run on demand for selected genotypes, not swept over an entire
    population every generation.
    """

    def __init__(
        self,
        mutation_operator: MutationOperator,
        behavioral_evaluator: Callable[[Genome], FloatArray],
        distance: DistanceMetric,
        num_samples: int = 16,
        fitness_evaluator: Callable[[Genome], float] | None = None,
        neutral_fitness_epsilon: float = 1e-6,
    ) -> None:
        if num_samples <= 0:
            raise ValueError("num_samples must be positive")
        if neutral_fitness_epsilon < 0:
            raise ValueError("neutral_fitness_epsilon must be >= 0")
        self._mutation_operator = mutation_operator
        self._behavioral_evaluator = behavioral_evaluator
        self._distance = distance
        self._num_samples = num_samples
        self._fitness_evaluator = fitness_evaluator
        self._neutral_fitness_epsilon = neutral_fitness_epsilon

    def analyze(self, genome: Genome, rng: np.random.Generator) -> EvolvabilityReport:
        baseline_signature = self._behavioral_evaluator(genome)
        baseline_fitness = self._fitness_evaluator(genome) if self._fitness_evaluator else None
        distances: list[float] = []
        fitness_deltas: list[float] = []
        num_viable = 0

        for _ in range(self._num_samples):
            mutant = self._mutation_operator.mutate(genome, rng)
            signature = self._evaluate_viability(mutant)
            if signature is None:
                continue
            num_viable += 1
            distances.append(self._distance.distance(signature, baseline_signature))
            if self._fitness_evaluator is not None and baseline_fitness is not None:
                fitness_deltas.append(self._fitness_evaluator(mutant) - baseline_fitness)

        mean_distance = float(np.mean(distances)) if distances else 0.0
        std_distance = float(np.std(distances)) if distances else 0.0

        fitness_distance_std = None
        beneficial_fraction = neutral_fraction = deleterious_fraction = None
        if self._fitness_evaluator is not None and fitness_deltas:
            eps = self._neutral_fitness_epsilon
            deltas = np.asarray(fitness_deltas)
            fitness_distance_std = float(np.std(deltas))
            beneficial_fraction = float(np.mean(deltas > eps))
            deleterious_fraction = float(np.mean(deltas < -eps))
            neutral_fraction = float(np.mean(np.abs(deltas) <= eps))

        return EvolvabilityReport(
            num_samples=self._num_samples,
            num_viable=num_viable,
            mean_behavioral_distance=mean_distance,
            behavioral_distance_std=std_distance,
            viable_fraction=num_viable / self._num_samples,
            fitness_distance_std=fitness_distance_std,
            beneficial_fraction=beneficial_fraction,
            neutral_fraction=neutral_fraction,
            deleterious_fraction=deleterious_fraction,
        )

    def _evaluate_viability(self, genome: Genome) -> FloatArray | None:
        """A mutant is "inviable" here if developing/evaluating it raises
        — e.g. a future mutation operator that can corrupt architecture-
        dependent shapes. The current `GaussianMutation` never produces
        shape errors, so every sample is viable in this first
        implementation; the hook exists for mutation operators that can
        break viability."""
        try:
            return self._behavioral_evaluator(genome)
        except Exception:
            return None
