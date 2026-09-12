"""Phase 16.1: the organism -> generation -> run/seed -> condition
aggregation layer.

The core rule this module exists to enforce: **the seed is the unit of
replication**. A `ContinuousEvolutionEngine`/`EvolutionEngine` run
produces many organisms, but they share one environment history, one
selection pressure, one RNG stream downstream of the seed — they are not
independent draws. Any function elsewhere in `genevra.population_analysis`
that runs a permutation test or bootstrap CI takes one value *per seed*,
never one value per organism. This module's job is exactly the reduction
step that makes that true: organism-level or generation-level values in,
one number per seed out.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence

import numpy as np


def reduce_within_seed(
    values: Sequence[float], reducer: Callable[[Sequence[float]], float]
) -> float:
    """Collapse many organism- or generation-level values from one seed
    into the single number that represents that seed in any downstream
    cross-seed statistical test."""
    if not values:
        raise ValueError("values must be non-empty")
    return reducer(values)


def seed_level_values(
    values_by_seed: Mapping[int, Sequence[float]],
    reducer: Callable[[Sequence[float]], float] = lambda v: float(np.mean(v)),
) -> dict[int, float]:
    """`{seed: [organism/generation values...]}` -> `{seed: one value}`.
    The returned dict's values, in seed order, are what
    `permutation_test`/`cohens_d`/`bootstrap_confidence_interval`
    (`genevra.analysis.aggregation`) should be called on — never the
    raw per-organism values."""
    return {seed: reduce_within_seed(values, reducer) for seed, values in values_by_seed.items()}


def to_condition_sample(values_by_seed: Mapping[int, float]) -> list[float]:
    """One condition's seed-level values as a plain list, in ascending
    seed order (deterministic ordering for reproducible test output)."""
    return [values_by_seed[seed] for seed in sorted(values_by_seed)]


__all__ = ["reduce_within_seed", "seed_level_values", "to_condition_sample"]
