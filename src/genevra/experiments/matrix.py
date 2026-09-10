"""Experiment matrix generation (Phase 9.11): `conditions x seeds x
environment regimes`, built from a base config factory and a set of named
transforms — no manual Python edits required to add a condition, regime,
or seed count. Produces a `conditions` dict shaped exactly like
`genevra.analysis.comparison.ComparisonRunner.conditions`, so execution
(sequential or safe-parallel) is never reimplemented here — build the
matrix, then hand it to `ComparisonRunner`.
"""

from __future__ import annotations

import dataclasses
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass

from genevra.evolution.engine import EvolutionConfig
from genevra.experiments.config import ExperimentConfig
from genevra.simulation.grid_world import GridWorldConfig

ConditionTransform = Callable[[EvolutionConfig], EvolutionConfig]


@dataclass(frozen=True)
class ExperimentMatrixResult:
    """`conditions` is ready to pass straight to `ComparisonRunner` (or to
    `ExperimentRunner` cell by cell). `seeds` is the shared seed sequence
    actually used across every cell — deterministic and identical per
    cell, matching `ComparisonRunner`'s "same seeds under every condition"
    contract, which is what keeps the matrix controlled rather than
    confounded."""

    conditions: dict[str, Callable[[int], ExperimentConfig]]
    seeds: tuple[int, ...]
    total_runs: int
    truncated: bool
    warnings: tuple[str, ...]


def build_experiment_matrix(
    base_config_factory: Callable[[int], ExperimentConfig],
    condition_transforms: Mapping[str, ConditionTransform],
    seeds: Sequence[int],
    environment_regimes: Mapping[str, GridWorldConfig] | None = None,
    max_runs: int | None = None,
) -> ExperimentMatrixResult:
    """`condition_transforms` maps a condition name to a function that
    rewrites the evolution config produced by `base_config_factory` (e.g.
    `genevra.experiments.conditions.apply_learning_condition` partially
    applied). `environment_regimes`, when given, additionally crosses
    every condition with a named environment override. `max_runs`, when
    given and exceeded, deterministically truncates the shared seed list
    (never silently drops specific cells) and records why in `warnings`
    rather than raising — callers that require the full matrix should
    check `truncated`."""
    if not condition_transforms:
        raise ValueError("at least one condition is required")
    if not seeds:
        raise ValueError("at least one seed is required")
    if max_runs is not None and max_runs < 1:
        raise ValueError("max_runs must be positive")

    regimes: dict[str, GridWorldConfig | None] = (
        dict(environment_regimes) if environment_regimes else {"": None}
    )
    num_cells = len(condition_transforms) * len(regimes)

    used_seeds = list(seeds)
    truncated = False
    warnings: list[str] = []
    total_requested = num_cells * len(seeds)
    if max_runs is not None and total_requested > max_runs:
        max_seeds_per_cell = max(1, max_runs // num_cells)
        used_seeds = list(seeds)[:max_seeds_per_cell]
        truncated = True
        warnings.append(
            f"matrix would require {total_requested} runs (> max_runs={max_runs}); "
            f"truncated to {max_seeds_per_cell} seed(s) per cell "
            f"({num_cells * max_seeds_per_cell} total runs)"
        )

    conditions: dict[str, Callable[[int], ExperimentConfig]] = {}
    for condition_name, transform in condition_transforms.items():
        for regime_name, regime_config in regimes.items():
            cell_name = f"{condition_name}__{regime_name}" if regime_name else condition_name
            conditions[cell_name] = _make_cell_factory(
                base_config_factory, transform, regime_config
            )

    return ExperimentMatrixResult(
        conditions=conditions,
        seeds=tuple(used_seeds),
        total_runs=len(conditions) * len(used_seeds),
        truncated=truncated,
        warnings=tuple(warnings),
    )


def _make_cell_factory(
    base_config_factory: Callable[[int], ExperimentConfig],
    transform: ConditionTransform,
    regime_config: GridWorldConfig | None,
) -> Callable[[int], ExperimentConfig]:
    def factory(seed: int) -> ExperimentConfig:
        base = base_config_factory(seed)
        new_evolution = transform(base.evolution)
        if regime_config is not None:
            new_evolution = dataclasses.replace(new_evolution, environment_config=regime_config)
        return dataclasses.replace(base, evolution=new_evolution)

    return factory


__all__ = ["ExperimentMatrixResult", "build_experiment_matrix", "ConditionTransform"]
