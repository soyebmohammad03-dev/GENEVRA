"""Phase 10.11 (`ReplicationRunner`) and Phase 10.14 (discovery/validation
seed splitting). Both share one concern: a pattern found in one set of
seeds must not be treated as robust until checked against seeds that
played no part in finding it.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field

import numpy as np

from genevra.analysis.aggregation import BootstrapCI, bootstrap_confidence_interval


@dataclass(frozen=True)
class SeedSplit:
    """A deterministic partition of a seed pool: `discovery_seeds` (used
    to find/generate a hypothesis) and `validation_seeds` (used only to
    check it). No randomness in the split itself — the caller's seed
    ordering is the only input, so the split is reproducible and
    auditable."""

    discovery_seeds: tuple[int, ...]
    validation_seeds: tuple[int, ...]

    def __post_init__(self) -> None:
        if set(self.discovery_seeds) & set(self.validation_seeds):
            raise ValueError("discovery_seeds and validation_seeds must not overlap")


def split_seeds(all_seeds: Sequence[int], discovery_fraction: float = 0.5) -> SeedSplit:
    if not 0.0 < discovery_fraction < 1.0:
        raise ValueError("discovery_fraction must be in (0, 1)")
    ordered = list(all_seeds)
    cut = max(1, round(len(ordered) * discovery_fraction))
    cut = min(cut, len(ordered) - 1) if len(ordered) > 1 else cut
    return SeedSplit(discovery_seeds=tuple(ordered[:cut]), validation_seeds=tuple(ordered[cut:]))


@dataclass(frozen=True)
class EvidenceSet:
    """One dependent-variable value per seed, from either the original
    (discovery) run or a replication run — never mixed together."""

    seeds: tuple[int, ...]
    values: tuple[float, ...]
    source: str

    def __post_init__(self) -> None:
        if len(self.seeds) != len(self.values):
            raise ValueError("seeds and values must be the same length")


@dataclass(frozen=True)
class ReplicationResult:
    hypothesis_id: str
    original: EvidenceSet
    replication: EvidenceSet
    original_mean: float
    replication_mean: float
    replication_ci: BootstrapCI
    replicated: bool
    note: str = field(
        default="'replicated' means the replication evidence's bootstrap CI excludes "
        "zero and agrees in sign with the original evidence — a necessary check, "
        "not proof the underlying effect is real or will hold under yet more seeds."
    )


class ReplicationRunner:
    """Compares `original` (discovery) evidence against `replication`
    evidence gathered under independent seeds. Raises if the two
    `EvidenceSet`s share any seed — replication evidence sharing seeds
    with the original is not independent replication."""

    def evaluate(
        self,
        hypothesis_id: str,
        original: EvidenceSet,
        replication: EvidenceSet,
        rng: np.random.Generator,
        confidence_level: float = 0.90,
    ) -> ReplicationResult:
        if set(original.seeds) & set(replication.seeds):
            raise ValueError("original and replication evidence must come from independent seeds")
        if len(replication.values) < 2:
            raise ValueError("replication requires at least 2 independent seed values")

        original_mean = float(np.mean(original.values))
        ci = bootstrap_confidence_interval(
            replication.values, rng, confidence_level=confidence_level
        )
        excludes_zero = ci.low > 0.0 or ci.high < 0.0
        same_sign = (ci.point_estimate > 0) == (original_mean > 0)
        replicated = excludes_zero and same_sign

        return ReplicationResult(
            hypothesis_id=hypothesis_id,
            original=original,
            replication=replication,
            original_mean=original_mean,
            replication_mean=ci.point_estimate,
            replication_ci=ci,
            replicated=replicated,
        )


__all__ = [
    "SeedSplit",
    "split_seeds",
    "EvidenceSet",
    "ReplicationResult",
    "ReplicationRunner",
]
