"""Phase 8.1-8.3 core research conditions, and a Phase 8.13 ablation
mechanism, expressed as small transforms over an existing `EvolutionConfig`
rather than new engine code — so a comparison across conditions/ablations
varies only the intended factor, everything else inherited unchanged from
the caller's base config.
"""

from __future__ import annotations

import dataclasses
from enum import Enum

import numpy as np

from genevra.evolution.engine import EvolutionConfig
from genevra.organism.learning import HebbianLearning, LearningRule, NoLearning
from genevra.organism.mutation import GaussianMutation
from genevra.simulation.dynamics import StaticDynamics


class LearningCondition(Enum):
    """GENEVRA's central three-way comparison (Phase 8.2/8.3/8.12):

    - `NO_LEARNING`: `NoLearning` — controller behavior never changes
      within a lifetime.
    - `FIXED_LEARNING`: `HebbianLearning` runs, but `learning_genes`
      never mutate — every individual, every generation, uses the same
      learning strategy the founders started with.
    - `EVOLVABLE_LEARNING`: `HebbianLearning` runs, and `learning_genes`
      are heritable and mutable like any other gene group.
    """

    NO_LEARNING = "no_learning"
    FIXED_LEARNING = "fixed_learning"
    EVOLVABLE_LEARNING = "evolvable_learning"


def apply_learning_condition(
    base: EvolutionConfig,
    condition: LearningCondition,
    learning_rule_factory: type[LearningRule] = HebbianLearning,
) -> EvolutionConfig:
    """Returns a copy of `base` configured for `condition`, changing only
    `learning_rule_factory` and the mutation operator's
    `mutate_learning_genes` flag. Requires
    `base.reproduction.mutation_operator` to be a `GaussianMutation` (the
    only mutation operator that supports this ablation today) — raises
    `TypeError` rather than silently ignoring a custom operator."""
    mutation_operator = base.reproduction.mutation_operator
    if not isinstance(mutation_operator, GaussianMutation):
        raise TypeError(
            "apply_learning_condition requires base.reproduction.mutation_operator "
            f"to be a GaussianMutation, got {type(mutation_operator).__name__}"
        )

    if condition is LearningCondition.NO_LEARNING:
        new_rule_factory: type[LearningRule] = NoLearning
        mutate_learning_genes = mutation_operator.mutate_learning_genes
    elif condition is LearningCondition.FIXED_LEARNING:
        new_rule_factory = learning_rule_factory
        mutate_learning_genes = False
    elif condition is LearningCondition.EVOLVABLE_LEARNING:
        new_rule_factory = learning_rule_factory
        mutate_learning_genes = True
    else:  # pragma: no cover - exhaustive Enum
        raise ValueError(f"unknown LearningCondition: {condition}")

    new_mutation_operator = GaussianMutation(
        mutate_learning_genes=mutate_learning_genes,
        mutate_mutation_genes=mutation_operator.mutate_mutation_genes,
    )
    new_reproduction = dataclasses.replace(
        base.reproduction, mutation_operator=new_mutation_operator
    )
    return dataclasses.replace(
        base, learning_rule_factory=new_rule_factory, reproduction=new_reproduction
    )


@dataclasses.dataclass(frozen=True)
class AblationConfig:
    """Phase 8.13: one mechanism disabled at a time, expressed as
    booleans so future ablations can be added as new fields here without
    touching `EvolutionEngine`. Only the ablations listed below are
    wired up by `apply_ablations`; toggling an unimplemented mechanism
    (memory, shared ecology, novelty pressure) is deliberately out of
    scope for this pass — see `docs/research_protocol.md` for why (each
    requires re-deriving controller input dimensions or swapping the
    environment/engine entirely, not just a config flag) — and is left
    for a future phase rather than half-implemented here.

    - `learning`: `False` -> `NoLearning` (equivalent to
      `LearningCondition.NO_LEARNING`).
    - `heritable_learning_params`: `False` -> learning genes fixed
      across generations (equivalent to `LearningCondition.FIXED_LEARNING`,
      only meaningful when `learning=True`).
    - `heritable_mutation_strength`: `False` -> mutation rate/sigma fixed
      at founder values across generations.
    - `changing_environment`: `False` -> environment dynamics forced to
      `StaticDynamics` at the environment's own configured regen rate,
      removing any `PeriodicDynamics`/`RegimeChangeDynamics`/
      `StochasticDynamics` the base config specified.
    """

    learning: bool = True
    heritable_learning_params: bool = True
    heritable_mutation_strength: bool = True
    changing_environment: bool = True


def apply_ablations(
    base: EvolutionConfig,
    ablations: AblationConfig,
    learning_rule_factory: type[LearningRule] = HebbianLearning,
) -> EvolutionConfig:
    mutation_operator = base.reproduction.mutation_operator
    if not isinstance(mutation_operator, GaussianMutation):
        raise TypeError(
            "apply_ablations requires base.reproduction.mutation_operator "
            f"to be a GaussianMutation, got {type(mutation_operator).__name__}"
        )

    new_rule_factory = base.learning_rule_factory if ablations.learning else NoLearning
    if ablations.learning and not ablations.heritable_learning_params:
        new_rule_factory = learning_rule_factory

    new_mutation_operator = GaussianMutation(
        mutate_learning_genes=(
            ablations.heritable_learning_params if ablations.learning else False
        ),
        mutate_mutation_genes=ablations.heritable_mutation_strength,
    )
    new_reproduction = dataclasses.replace(
        base.reproduction, mutation_operator=new_mutation_operator
    )

    new_environment = base.environment_config
    if not ablations.changing_environment and base.environment_config.dynamics is not None:
        static_regime = base.environment_config.dynamics.regime_at(0, np.random.default_rng(0))
        new_environment = dataclasses.replace(
            base.environment_config, dynamics=StaticDynamics(static_regime)
        )

    return dataclasses.replace(
        base,
        learning_rule_factory=new_rule_factory,
        reproduction=new_reproduction,
        environment_config=new_environment,
    )
