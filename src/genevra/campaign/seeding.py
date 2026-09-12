"""Phase 17.3: hierarchical deterministic seed derivation.

`numpy.random.SeedSequence.spawn` is the stdlib-adjacent (numpy-provided)
tool purpose-built for exactly this: deriving N independent, reproducible
child streams from one root seed, and children-of-children for a second
level. No hand-rolled hashing is needed. The hierarchy is:

    campaign seed
        -> condition seed  (one child per condition, in declared order)
            -> replicate seed  (one grandchild per seed index)

`derive_condition_seeds`/`derive_replicate_seed` are pure functions of
(campaign_seed, condition_index, replicate_index) — calling them twice
with the same arguments always returns the same integer, and changing one
condition's position does not change any other condition's stream only if
the *number and order* of conditions is unchanged (spawning is
order-dependent, like drawing N items from one RNG in sequence; this is
documented, not hidden, in docs/research_campaigns.md).
"""

from __future__ import annotations

import numpy as np


def _spawn_seeds(parent: np.random.SeedSequence, n: int) -> list[int]:
    return [int(child.generate_state(1)[0]) for child in parent.spawn(n)]


def derive_condition_seeds(campaign_seed: int, n_conditions: int) -> list[int]:
    """One independent seed per condition, in declared order."""
    return _spawn_seeds(np.random.SeedSequence(campaign_seed), n_conditions)


def derive_replicate_seeds(condition_seed: int, n_replicates: int) -> list[int]:
    """One independent seed per replicate (run) within a condition."""
    return _spawn_seeds(np.random.SeedSequence(condition_seed), n_replicates)


def derive_run_seed(campaign_seed: int, condition_index: int, replicate_index: int) -> int:
    """The seed for one specific (condition, replicate) cell — computed
    via the same two-step `derive_condition_seeds` ->
    `derive_replicate_seeds` path as the full derivation, just truncated
    to the one cell needed (prefix-stable, see
    `test_prefix_stability_more_conditions_does_not_change_earlier_ones`)."""
    condition_seed = derive_condition_seeds(campaign_seed, condition_index + 1)[condition_index]
    return derive_replicate_seeds(condition_seed, replicate_index + 1)[replicate_index]


__all__ = ["derive_condition_seeds", "derive_replicate_seeds", "derive_run_seed"]
