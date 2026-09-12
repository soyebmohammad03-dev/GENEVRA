"""Phase 13.5: generalization across environments, distinguished by
environment category rather than a single "generalization score."

Categories (Phase 13.5's TRAIN/SEEN/RECURRENT/RELATED-UNSEEN/NOVEL
list, adapted to what GENEVRA's `GridWorldConfig` can actually vary):

- ``train``: the exact config and distribution the genome evolved under.
- ``recurrent``: the same config, a new environment seed — a
  distributionally identical but literally unseen instance, the
  "recurrent environment" case.
- ``related_unseen``: one `GridWorldConfig` parameter (resource or
  obstacle density) shifted by a moderate amount.
- ``novel``: multiple parameters shifted substantially, and/or grid
  dimensions changed.

This module also provides a canalization proxy (Phase 13.9): the
variance of one genome's behavioral signature across environment
categories at fixed genotype. GENEVRA has no gene-regulatory-network
model, so this is the only canalization-adjacent measurement currently
possible — documented as a proxy, not a claim of measuring canalization
in the developmental-biology sense.
"""

from __future__ import annotations

import dataclasses
from dataclasses import dataclass, field
from typing import Any

import numpy as np

from genevra.evolution.fitness import FitnessFunction
from genevra.evolution.lifetime import run_single_lifetime
from genevra.mechanisms.definitions import GENERALIZATION_DEFINITION, MetricDefinition
from genevra.metrics.adaptation import AdaptationCurve, compute_adaptation_curve
from genevra.metrics.behavior import behavioral_signature
from genevra.metrics.diversity import DistanceMetric
from genevra.organism.genome import Genome
from genevra.organism.learning import LearningRule
from genevra.organism.organism import OrganismConfig
from genevra.simulation.grid_world import GridWorldConfig

_LIMITATION_NOTE = (
    "'Novel' here means a parameter shift within GridWorld's own model, not a "
    "qualitatively different environment class. Retention > 1 means the tested "
    "environment scored higher than the train environment for this one genome; it "
    "is not evidence of a general generalization capacity."
)


@dataclass(frozen=True)
class EnvironmentResult:
    category: str
    fitness: float
    adaptation: AdaptationCurve
    behavioral_distance_from_train: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "category": self.category,
            "fitness": self.fitness,
            "adaptation": dataclasses.asdict(self.adaptation),
            "behavioral_distance_from_train": self.behavioral_distance_from_train,
        }


@dataclass(frozen=True)
class GeneralizationProfile:
    train: EnvironmentResult
    results: tuple[EnvironmentResult, ...]
    """One entry per non-train environment category tested."""
    definition: MetricDefinition = field(default=GENERALIZATION_DEFINITION)
    limitation_note: str = field(default=_LIMITATION_NOTE)

    def retention(self, category: str) -> float | None:
        for result in self.results:
            if result.category == category and self.train.fitness != 0.0:
                return result.fitness / self.train.fitness
        return None

    def to_dict(self) -> dict[str, Any]:
        return {
            "train": self.train.to_dict(),
            "results": [r.to_dict() for r in self.results],
            "retention": {r.category: self.retention(r.category) for r in self.results},
            "definition": self.definition.to_dict(),
            "limitation_note": self.limitation_note,
        }


def _perturb_density(
    config: GridWorldConfig, resource_delta: float, obstacle_delta: float
) -> GridWorldConfig:
    return dataclasses.replace(
        config,
        resource_density=float(np.clip(config.resource_density + resource_delta, 0.0, 1.0)),
        obstacle_density=float(np.clip(config.obstacle_density + obstacle_delta, 0.0, 1.0)),
    )


def default_related_unseen_config(train_config: GridWorldConfig) -> GridWorldConfig:
    return _perturb_density(train_config, resource_delta=-0.03, obstacle_delta=0.03)


def default_novel_config(train_config: GridWorldConfig) -> GridWorldConfig:
    perturbed = _perturb_density(train_config, resource_delta=-0.06, obstacle_delta=0.08)
    return dataclasses.replace(perturbed, width=max(3, train_config.width + 4))


class GeneralizationAnalyzer:
    def __init__(
        self,
        organism_config: OrganismConfig,
        learning_rule: LearningRule,
        fitness_function: FitnessFunction,
        distance: DistanceMetric,
        max_steps: int = 100,
        adaptation_window: int = 10,
    ) -> None:
        self._organism_config = organism_config
        self._learning_rule = learning_rule
        self._fitness_function = fitness_function
        self._distance = distance
        self._max_steps = max_steps
        self._adaptation_window = adaptation_window

    def _evaluate(
        self, genome: Genome, environment_config: GridWorldConfig, env_seed: int, organism_seed: int
    ) -> tuple[float, AdaptationCurve, np.ndarray[Any, Any]]:
        observations = run_single_lifetime(
            genome,
            environment_config,
            self._organism_config,
            self._learning_rule,
            env_seed,
            organism_seed,
            self._max_steps,
        )
        fitness = self._fitness_function.compute(observations)
        adaptation = compute_adaptation_curve(observations, window=self._adaptation_window)
        signature = behavioral_signature(observations)
        return fitness, adaptation, signature

    def analyze(
        self,
        genome: Genome,
        train_config: GridWorldConfig,
        rng: np.random.Generator,
        related_unseen_config: GridWorldConfig | None = None,
        novel_config: GridWorldConfig | None = None,
    ) -> GeneralizationProfile:
        train_fitness, train_adaptation, train_signature = self._evaluate(
            genome, train_config, int(rng.integers(0, 2**31 - 1)), int(rng.integers(0, 2**31 - 1))
        )
        train_result = EnvironmentResult(
            category="train",
            fitness=train_fitness,
            adaptation=train_adaptation,
            behavioral_distance_from_train=0.0,
        )

        categories: dict[str, GridWorldConfig] = {
            "recurrent": train_config,
            "related_unseen": related_unseen_config or default_related_unseen_config(train_config),
            "novel": novel_config or default_novel_config(train_config),
        }
        results = []
        for category, config in categories.items():
            fitness, adaptation, signature = self._evaluate(
                genome, config, int(rng.integers(0, 2**31 - 1)), int(rng.integers(0, 2**31 - 1))
            )
            results.append(
                EnvironmentResult(
                    category=category,
                    fitness=fitness,
                    adaptation=adaptation,
                    behavioral_distance_from_train=self._distance.distance(
                        signature, train_signature
                    ),
                )
            )
        return GeneralizationProfile(train=train_result, results=tuple(results))


def canalization_proxy(profile: GeneralizationProfile) -> float:
    """Phase 13.9: variance of `behavioral_distance_from_train` across
    tested environment categories, for one fixed genotype. Low variance
    (behavior barely changes across environments) is the operational
    proxy for canalization used here; high variance is labeled flexible.
    This is NOT a developmental-biology canalization measurement — GENEVRA
    has no gene-regulatory network whose expression could be buffered
    against perturbation, only a fixed feedforward controller plus
    lifetime learning, so this proxy can only speak to *behavioral*
    stability across tested environments, not developmental buffering."""
    if not profile.results:
        return 0.0
    distances = [r.behavioral_distance_from_train for r in profile.results]
    return float(np.var(distances))


__all__ = [
    "EnvironmentResult",
    "GeneralizationProfile",
    "GeneralizationAnalyzer",
    "default_related_unseen_config",
    "default_novel_config",
    "canalization_proxy",
]
