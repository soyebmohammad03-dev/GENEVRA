"""Counterfactual mutation analysis (Phase 9.9/9.10): "what happens if a
specific heritable learning mechanism is perturbed by a controlled
amount," rather than `EvolvabilityAnalyzer`'s "what variation does random
mutation produce." Shares that module's injected-evaluator pattern
deliberately (same shape of caller-supplied `Genome -> FloatArray` /
`Genome -> float` callbacks) so behavior/fitness evaluation is never
duplicated.

**Mechanism vs outcome (Phase 9.10).** Every `CounterfactualResult` keeps
the *mechanism* (which gene was perturbed, and by how much) and the
*outcome* (the measured behavioral/fitness/novelty consequence) as
separate fields. This module never concludes the mechanism *caused* the
outcome — that requires the selection/generational process this single-
genotype, single-step analysis does not perform. See
`_LIMITATION_NOTE`.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass, field

import numpy as np

from genevra.arrays import FloatArray
from genevra.metrics.diversity import DistanceMetric
from genevra.organism.genome import Genome

_LIMITATION_NOTE = (
    "A CounterfactualResult reports the measured consequence of one controlled "
    "perturbation to one genotype's learning genes. It is controlled-perturbation "
    "analysis, not causal proof: it does not establish that this mechanism drives "
    "the outcome across a population, under selection, or across other genotypes — "
    "only that changing it changed the outcome for this genotype under this "
    "evaluation. Treat it as one input to a larger analysis (e.g. a proposed "
    "follow-up experiment), not a conclusion."
)

_GENE_NAMES: tuple[str, ...] = ("learning_rate", "plasticity_gate", "decay")


@dataclass(frozen=True)
class Perturbation:
    """The mechanism half of a counterfactual: which learning gene to
    change and by how much. `gene` must be one of `_GENE_NAMES` — every
    perturbation must correspond to an actually-implemented mechanism
    (Phase 9.1's constraint), not an arbitrary vector edit."""

    gene: str
    delta: float
    description: str = ""

    def __post_init__(self) -> None:
        if self.gene not in _GENE_NAMES:
            raise ValueError(f"gene must be one of {_GENE_NAMES}, got {self.gene!r}")

    def label(self) -> str:
        return self.description or f"{self.gene}{'+' if self.delta >= 0 else ''}{self.delta:g}"


@dataclass(frozen=True)
class CounterfactualResult:
    mechanism: Perturbation
    fitness_delta: float | None
    behavioral_distance: float
    novelty_delta: float | None
    viable: bool
    limitation_note: str = field(default=_LIMITATION_NOTE)


class CounterfactualAnalyzer:
    """Applies each `Perturbation` to a copy of `genome.learning_genes`
    (never the original organism/genome — Phase 9.9's requirement), then
    compares the perturbed variant's behavior/fitness/novelty against the
    unperturbed baseline using the same injected-callback pattern as
    `genevra.metrics.evolvability.EvolvabilityAnalyzer`."""

    def __init__(
        self,
        behavioral_evaluator: Callable[[Genome], FloatArray],
        distance: DistanceMetric,
        fitness_evaluator: Callable[[Genome], float] | None = None,
        novelty_evaluator: Callable[[Genome], float] | None = None,
    ) -> None:
        self._behavioral_evaluator = behavioral_evaluator
        self._distance = distance
        self._fitness_evaluator = fitness_evaluator
        self._novelty_evaluator = novelty_evaluator

    def analyze(
        self, genome: Genome, perturbations: Sequence[Perturbation]
    ) -> list[CounterfactualResult]:
        baseline_signature = self._behavioral_evaluator(genome)
        baseline_fitness = self._fitness_evaluator(genome) if self._fitness_evaluator else None
        baseline_novelty = self._novelty_evaluator(genome) if self._novelty_evaluator else None

        results = []
        for perturbation in perturbations:
            variant = _apply_perturbation(genome, perturbation)
            try:
                signature = self._behavioral_evaluator(variant)
            except Exception:
                results.append(
                    CounterfactualResult(
                        mechanism=perturbation,
                        fitness_delta=None,
                        behavioral_distance=0.0,
                        novelty_delta=None,
                        viable=False,
                    )
                )
                continue

            fitness_delta = (
                self._fitness_evaluator(variant) - baseline_fitness
                if self._fitness_evaluator is not None and baseline_fitness is not None
                else None
            )
            novelty_delta = (
                self._novelty_evaluator(variant) - baseline_novelty
                if self._novelty_evaluator is not None and baseline_novelty is not None
                else None
            )
            results.append(
                CounterfactualResult(
                    mechanism=perturbation,
                    fitness_delta=fitness_delta,
                    behavioral_distance=self._distance.distance(signature, baseline_signature),
                    novelty_delta=novelty_delta,
                    viable=True,
                )
            )
        return results


def _apply_perturbation(genome: Genome, perturbation: Perturbation) -> Genome:
    """Returns a new `Genome` with one `learning_genes` entry shifted by
    `perturbation.delta`; the original genome is never mutated in
    place."""
    index = _GENE_NAMES.index(perturbation.gene)
    new_learning_genes: FloatArray = genome.learning_genes.copy()
    new_learning_genes[index] = new_learning_genes[index] + perturbation.delta
    return Genome(
        architecture=genome.architecture,
        controller_weights=genome.controller_weights,
        metabolic_genes=genome.metabolic_genes,
        mutation_genes=genome.mutation_genes,
        learning_genes=new_learning_genes.astype(np.float32),
    )


__all__ = [
    "Perturbation",
    "CounterfactualResult",
    "CounterfactualAnalyzer",
]
