"""Phase 13.2: robustness as preservation under a controlled
perturbation, measured along four independent dimensions rather than
one "robustness score."

Robustness is not fitness: a genotype can be highly robust (nearly
identical outcomes under every tested perturbation) while performing
poorly, or fragile while performing well. Every dimension below reports
a *distribution* (mean, std, 10th percentile) of a distance/delta from
an unperturbed baseline, never only a mean — Phase 13.2's requirement to
track lower-tail behavior, not just central tendency.
"""

from __future__ import annotations

import dataclasses
from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Any

import numpy as np

from genevra.arrays import FloatArray
from genevra.evolution.fitness import FitnessFunction
from genevra.evolution.lifetime import run_single_lifetime
from genevra.mechanisms.definitions import ROBUSTNESS_DEFINITION, MetricDefinition
from genevra.metrics.behavior import behavioral_signature
from genevra.metrics.diversity import DistanceMetric
from genevra.organism.genome import Genome
from genevra.organism.learning import LearningRule, NoLearning
from genevra.organism.mutation import MutationOperator
from genevra.organism.organism import OrganismConfig
from genevra.simulation.grid_world import GridWorldConfig

_LIMITATION_NOTE = (
    "Each dimension is a sampled distribution of one perturbation kind's effect on "
    "one genotype, not an exhaustive or population-level measurement. Robustness is "
    "reported independently of fitness by design."
)


@dataclass(frozen=True)
class RobustnessDimensionResult:
    dimension: str
    n_samples: int
    mean: float
    std: float
    p10: float
    values: tuple[float, ...]
    limitation_note: str = field(default=_LIMITATION_NOTE)

    def to_dict(self) -> dict[str, Any]:
        return dataclasses.asdict(self)


def _summarize(name: str, values: Sequence[float]) -> RobustnessDimensionResult:
    if not values:
        return RobustnessDimensionResult(
            dimension=name, n_samples=0, mean=0.0, std=0.0, p10=0.0, values=()
        )
    arr = np.asarray(values, dtype=np.float64)
    return RobustnessDimensionResult(
        dimension=name,
        n_samples=len(values),
        mean=float(np.mean(arr)),
        std=float(np.std(arr)),
        p10=float(np.percentile(arr, 10)),
        values=tuple(float(v) for v in values),
    )


@dataclass(frozen=True)
class RobustnessProfile:
    genetic: RobustnessDimensionResult
    behavioral: RobustnessDimensionResult
    fitness: RobustnessDimensionResult | None
    environmental: RobustnessDimensionResult | None
    learning_amplification: float | None
    """behavioral.mean measured with the organism's actual learning rule
    minus the same measurement with `NoLearning()` substituted, holding
    every seed fixed pairwise. Positive: this genotype's behavior varies
    *more* across repeated stochastic lifetimes when lifetime learning is
    active than when it is disabled — i.e. learning is a source of
    behavioral variability here, not a claim about learning's robustness
    in general. `None` when not requested."""
    definition: MetricDefinition = field(default=ROBUSTNESS_DEFINITION)

    def to_dict(self) -> dict[str, Any]:
        return {
            "genetic": self.genetic.to_dict(),
            "behavioral": self.behavioral.to_dict(),
            "fitness": self.fitness.to_dict() if self.fitness else None,
            "environmental": self.environmental.to_dict() if self.environmental else None,
            "learning_amplification": self.learning_amplification,
            "definition": self.definition.to_dict(),
        }


class RobustnessAnalyzer:
    """Runs all four perturbation kinds against one genome. Reuses
    `run_single_lifetime` directly (the same function
    `genevra.metrics.evolvability.EvolvabilityAnalyzer` wraps behind an
    injected callback) rather than a second lifetime-execution path."""

    def __init__(
        self,
        environment_config: GridWorldConfig,
        organism_config: OrganismConfig,
        learning_rule: LearningRule,
        mutation_operator: MutationOperator,
        distance: DistanceMetric,
        fitness_function: FitnessFunction | None = None,
        num_samples: int = 10,
        max_steps: int = 100,
    ) -> None:
        if num_samples <= 0:
            raise ValueError("num_samples must be positive")
        self._environment_config = environment_config
        self._organism_config = organism_config
        self._learning_rule = learning_rule
        self._mutation_operator = mutation_operator
        self._distance = distance
        self._fitness_function = fitness_function
        self._num_samples = num_samples
        self._max_steps = max_steps

    def _run(
        self, genome: Genome, learning_rule: LearningRule, env_seed: int, organism_seed: int
    ) -> FloatArray:
        observations = run_single_lifetime(
            genome,
            self._environment_config,
            self._organism_config,
            learning_rule,
            env_seed,
            organism_seed,
            self._max_steps,
        )
        return behavioral_signature(observations)

    def analyze(
        self,
        genome: Genome,
        rng: np.random.Generator,
        environmental_perturbations: Sequence[GridWorldConfig] = (),
        include_learning_amplification: bool = False,
    ) -> RobustnessProfile:
        base_env_seed = int(rng.integers(0, 2**31 - 1))
        base_org_seed = int(rng.integers(0, 2**31 - 1))
        baseline_signature = self._run(genome, self._learning_rule, base_env_seed, base_org_seed)
        baseline_fitness = (
            self._fitness_function.compute(
                run_single_lifetime(
                    genome,
                    self._environment_config,
                    self._organism_config,
                    self._learning_rule,
                    base_env_seed,
                    base_org_seed,
                    self._max_steps,
                )
            )
            if self._fitness_function is not None
            else None
        )

        genetic_distances: list[float] = []
        fitness_deltas: list[float] = []
        for _ in range(self._num_samples):
            mutant = self._mutation_operator.mutate(genome, rng)
            env_seed = int(rng.integers(0, 2**31 - 1))
            org_seed = int(rng.integers(0, 2**31 - 1))
            signature = self._run(mutant, self._learning_rule, env_seed, org_seed)
            genetic_distances.append(self._distance.distance(signature, baseline_signature))
            if self._fitness_function is not None and baseline_fitness is not None:
                obs = run_single_lifetime(
                    mutant,
                    self._environment_config,
                    self._organism_config,
                    self._learning_rule,
                    env_seed,
                    org_seed,
                    self._max_steps,
                )
                fitness_deltas.append(abs(self._fitness_function.compute(obs) - baseline_fitness))

        behavioral_distances: list[float] = []
        for _ in range(self._num_samples):
            env_seed = int(rng.integers(0, 2**31 - 1))
            org_seed = int(rng.integers(0, 2**31 - 1))
            signature = self._run(genome, self._learning_rule, env_seed, org_seed)
            behavioral_distances.append(self._distance.distance(signature, baseline_signature))

        environmental_result: RobustnessDimensionResult | None = None
        if environmental_perturbations and self._fitness_function is not None:
            env_fitness_deltas: list[float] = []
            for perturbed_env in environmental_perturbations:
                env_seed = int(rng.integers(0, 2**31 - 1))
                org_seed = int(rng.integers(0, 2**31 - 1))
                obs = run_single_lifetime(
                    genome,
                    perturbed_env,
                    self._organism_config,
                    self._learning_rule,
                    env_seed,
                    org_seed,
                    self._max_steps,
                )
                perturbed_fitness = self._fitness_function.compute(obs)
                if baseline_fitness is not None:
                    env_fitness_deltas.append(abs(perturbed_fitness - baseline_fitness))
            environmental_result = _summarize("environmental", env_fitness_deltas)

        learning_amplification: float | None = None
        if include_learning_amplification and not isinstance(self._learning_rule, NoLearning):
            baseline_no_learning = self._run(genome, NoLearning(), base_env_seed, base_org_seed)
            no_learning_distances: list[float] = []
            for _ in range(self._num_samples):
                env_seed = int(rng.integers(0, 2**31 - 1))
                org_seed = int(rng.integers(0, 2**31 - 1))
                signature = self._run(genome, NoLearning(), env_seed, org_seed)
                no_learning_distances.append(
                    self._distance.distance(signature, baseline_no_learning)
                )
            with_learning_mean = (
                float(np.mean(behavioral_distances)) if behavioral_distances else 0.0
            )
            without_learning_mean = (
                float(np.mean(no_learning_distances)) if no_learning_distances else 0.0
            )
            learning_amplification = with_learning_mean - without_learning_mean

        return RobustnessProfile(
            genetic=_summarize("genetic", genetic_distances),
            behavioral=_summarize("behavioral", behavioral_distances),
            fitness=_summarize("fitness", fitness_deltas) if self._fitness_function else None,
            environmental=environmental_result,
            learning_amplification=learning_amplification,
        )


def robustness_evolvability_association(
    robustness_scores: Sequence[float], evolvability_scores: Sequence[float]
) -> float | None:
    """Pearson correlation between a per-genotype robustness measurement
    (e.g. `RobustnessProfile.genetic.mean`, lower = more robust) and a
    per-genotype evolvability measurement (e.g.
    `EvolvabilityReport.mean_behavioral_distance`), across a sampled set
    of genotypes. Phase 13.3: reports association only. `None` if fewer
    than 3 paired observations or either series is constant — the same
    threshold and non-fabrication convention as
    `genevra.analysis.tradeoff.summarize_tradeoff`. This function takes
    no position on H1 ("robustness increases evolvability"), H2 (the
    opposite), or H3 (nonlinear) — the caller interprets the sign and a
    scatter of the raw values, not this function.
    """
    if len(robustness_scores) != len(evolvability_scores):
        raise ValueError("robustness_scores and evolvability_scores must be the same length")
    if len(robustness_scores) < 3:
        return None
    a = np.asarray(robustness_scores, dtype=np.float64)
    b = np.asarray(evolvability_scores, dtype=np.float64)
    if np.std(a) == 0.0 or np.std(b) == 0.0:
        return None
    return float(np.corrcoef(a, b)[0, 1])


__all__ = [
    "RobustnessDimensionResult",
    "RobustnessProfile",
    "RobustnessAnalyzer",
    "robustness_evolvability_association",
]
