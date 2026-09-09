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
    num_samples: int
    num_viable: int
    mean_behavioral_distance: float
    behavioral_distance_std: float
    viable_fraction: float
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
    ) -> None:
        if num_samples <= 0:
            raise ValueError("num_samples must be positive")
        self._mutation_operator = mutation_operator
        self._behavioral_evaluator = behavioral_evaluator
        self._distance = distance
        self._num_samples = num_samples

    def analyze(self, genome: Genome, rng: np.random.Generator) -> EvolvabilityReport:
        baseline_signature = self._behavioral_evaluator(genome)
        distances: list[float] = []
        num_viable = 0

        for _ in range(self._num_samples):
            mutant = self._mutation_operator.mutate(genome, rng)
            signature = self._evaluate_viability(mutant)
            if signature is None:
                continue
            num_viable += 1
            distances.append(self._distance.distance(signature, baseline_signature))

        mean_distance = float(np.mean(distances)) if distances else 0.0
        std_distance = float(np.std(distances)) if distances else 0.0
        return EvolvabilityReport(
            num_samples=self._num_samples,
            num_viable=num_viable,
            mean_behavioral_distance=mean_distance,
            behavioral_distance_std=std_distance,
            viable_fraction=num_viable / self._num_samples,
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
