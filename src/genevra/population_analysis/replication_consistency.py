"""Phase 16.8: independent-replication consistency.

A general-purpose sibling of `genevra.discovery.replication`
(`ReplicationRunner`'s discovery/confirmation-split protocol) for the
simpler, more common case: N independent seeds already each produced one
effect estimate for the same comparison, and the question is how
consistent that effect is across seeds — never whether pooling all seeds
together looks significant. Pooled significance can hide substantial
seed-to-seed disagreement; this module reports that disagreement
explicitly rather than only a pooled p-value.
"""

from __future__ import annotations

import dataclasses
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ReplicationConsistencyReport:
    n_seeds: int
    per_seed_effect: dict[int, float]
    majority_sign: float | None
    """+1.0 or -1.0: the sign held by the majority of seeds. `None` if
    tied or fewer than 2 seeds."""
    agreement_fraction: float | None
    """Fraction of seeds whose effect sign matches `majority_sign`. 1.0 =
    every seed agrees in direction; low values indicate a heterogeneous,
    seed-dependent effect that pooled significance alone would not show."""
    sign_reversals: int
    """Count of seeds whose sign is opposite the majority."""

    def to_dict(self) -> dict[str, Any]:
        return dataclasses.asdict(self)


def summarize_replication_consistency(
    effect_by_seed: Mapping[int, float],
) -> ReplicationConsistencyReport:
    if not effect_by_seed:
        return ReplicationConsistencyReport(0, {}, None, None, 0)
    effects = dict(effect_by_seed)
    signs = {seed: (1.0 if v > 0 else (-1.0 if v < 0 else 0.0)) for seed, v in effects.items()}
    nonzero = [s for s in signs.values() if s != 0.0]
    if not nonzero:
        return ReplicationConsistencyReport(len(effects), effects, None, None, 0)
    positive = sum(1 for s in nonzero if s > 0)
    negative = len(nonzero) - positive
    majority_sign = 1.0 if positive >= negative else -1.0
    agreeing = sum(1 for s in nonzero if s == majority_sign)
    reversals = len(nonzero) - agreeing
    return ReplicationConsistencyReport(
        n_seeds=len(effects),
        per_seed_effect=effects,
        majority_sign=majority_sign,
        agreement_fraction=agreeing / len(nonzero),
        sign_reversals=reversals,
    )


__all__ = ["ReplicationConsistencyReport", "summarize_replication_consistency"]
