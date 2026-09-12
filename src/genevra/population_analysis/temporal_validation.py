"""Phase 16.5: temporal cross-validation — a genuine train/test split
over generations, not a relabeling of a full-trajectory correlation.

Two variants, both provided because they answer different questions:

1. `within_seed_holdout`: fit a linear relationship on one seed's early
   generations, check whether its *sign* holds on that same seed's later
   (held-out) generations. Weaker (still one autocorrelated trajectory)
   but always available with a single seed.
2. `leave_one_seed_out`: fit on N-1 seeds' full trajectories, check
   whether the sign holds on the left-out seed. The genuinely
   independent-replication version of temporal validation (Phase 16.5's
   stronger example), requires >= 3 seeds.
"""

from __future__ import annotations

import dataclasses
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

import numpy as np


@dataclass(frozen=True)
class LinearFit:
    slope: float
    intercept: float


def _fit(x: Sequence[float], y: Sequence[float]) -> LinearFit | None:
    if len(x) < 2 or np.std(x) == 0.0:
        return None
    slope, intercept = np.polyfit(
        np.asarray(x, dtype=np.float64), np.asarray(y, dtype=np.float64), 1
    )
    return LinearFit(float(slope), float(intercept))


@dataclass(frozen=True)
class HoldoutResult:
    train_fit: LinearFit | None
    held_out_sign_matches: bool | None
    """Whether the *sign* of the actual x->y relationship in the held-out
    segment (a simple correlation sign, not a second regression) matches
    the sign the train-segment fit predicted. `None` if either segment
    lacks the variation needed to determine a sign."""

    def to_dict(self) -> dict[str, Any]:
        return {
            "train_fit": dataclasses.asdict(self.train_fit) if self.train_fit else None,
            "held_out_sign_matches": self.held_out_sign_matches,
        }


def _sign_of_relationship(x: Sequence[float], y: Sequence[float]) -> float | None:
    if len(x) < 2 or np.std(x) == 0.0 or np.std(y) == 0.0:
        return None
    return float(np.sign(np.corrcoef(x, y)[0, 1]))


def within_seed_holdout(
    x: Sequence[float], y: Sequence[float], split_fraction: float = 0.5
) -> HoldoutResult:
    if not 0.0 < split_fraction < 1.0:
        raise ValueError("split_fraction must be in (0, 1)")
    n = min(len(x), len(y))
    split = int(n * split_fraction)
    if split < 2 or n - split < 2:
        return HoldoutResult(None, None)
    train_fit = _fit(x[:split], y[:split])
    test_sign = _sign_of_relationship(x[split:n], y[split:n])
    if train_fit is None or test_sign is None:
        return HoldoutResult(train_fit, None)
    return HoldoutResult(train_fit, bool(np.sign(train_fit.slope) == test_sign))


@dataclass(frozen=True)
class LeaveOneSeedOutResult:
    n_seeds: int
    held_out_sign_matches_by_seed: dict[int, bool | None]
    agreement_rate: float | None
    """Fraction of held-out seeds where the train-fit sign matched the
    held-out seed's own relationship sign — `None` if fewer than 3 seeds
    were supplied (Phase 16.5 requires an actual holdout, not a 1- or
    2-seed degenerate case)."""

    def to_dict(self) -> dict[str, Any]:
        return {
            "n_seeds": self.n_seeds,
            "held_out_sign_matches_by_seed": self.held_out_sign_matches_by_seed,
            "agreement_rate": self.agreement_rate,
        }


def leave_one_seed_out(
    x_by_seed: Mapping[int, Sequence[float]], y_by_seed: Mapping[int, Sequence[float]]
) -> LeaveOneSeedOutResult:
    seeds = sorted(set(x_by_seed) & set(y_by_seed))
    if len(seeds) < 3:
        return LeaveOneSeedOutResult(len(seeds), {}, None)
    results: dict[int, bool | None] = {}
    for held_out in seeds:
        train_seeds = [s for s in seeds if s != held_out]
        train_x = [v for s in train_seeds for v in x_by_seed[s]]
        train_y = [v for s in train_seeds for v in y_by_seed[s]]
        train_fit = _fit(train_x, train_y)
        test_sign = _sign_of_relationship(x_by_seed[held_out], y_by_seed[held_out])
        if train_fit is None or test_sign is None:
            results[held_out] = None
        else:
            results[held_out] = bool(np.sign(train_fit.slope) == test_sign)
    determined = [v for v in results.values() if v is not None]
    agreement = sum(determined) / len(determined) if determined else None
    return LeaveOneSeedOutResult(len(seeds), results, agreement)


__all__ = [
    "LinearFit",
    "HoldoutResult",
    "within_seed_holdout",
    "LeaveOneSeedOutResult",
    "leave_one_seed_out",
]
