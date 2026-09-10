"""Phase 10.13: multiple-comparisons awareness for the discovery engine.

Whenever `genevra.discovery.correlation` or the hypothesis-generation
pipeline examines many relationships at once, the smallest p-value out of
many tests is not itself meaningful — some tests will look "significant"
by chance alone as the number of comparisons grows. This module applies
the Benjamini-Hochberg false discovery rate (FDR) procedure (a standard,
lightweight correction; no dependency beyond numpy) and labels each
result `exploratory` or `confirmatory` so callers never silently treat a
mined correlation as a pre-registered test.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass


@dataclass(frozen=True)
class FDRResult:
    p_value: float
    q_value: float
    """Benjamini-Hochberg adjusted p-value ("q-value"): the smallest FDR
    threshold at which this comparison would be called significant."""
    significant: bool
    label: str
    """`"confirmatory"` if this comparison was declared in advance as a
    primary analysis (`is_primary=True`), otherwise `"exploratory"` —
    Phase 10.13's requirement to distinguish pre-specified primary
    analyses from data-mined ones, regardless of q-value."""


def benjamini_hochberg(
    p_values: Sequence[float],
    is_primary: Sequence[bool] | None = None,
    alpha: float = 0.05,
) -> list[FDRResult]:
    """Standard BH step-up procedure: sort p-values ascending, find the
    largest `k` such that `p_(k) <= (k / m) * alpha`, declare everything
    up to `k` significant. `is_primary`, when given, only affects the
    `label` field (exploratory vs. confirmatory) — every p-value is still
    corrected together as one family, since that is what "many
    relationships examined" (Phase 10.13) means here."""
    if not p_values:
        return []
    if not 0.0 < alpha < 1.0:
        raise ValueError("alpha must be in (0, 1)")
    primary_flags = list(is_primary) if is_primary is not None else [False] * len(p_values)
    if len(primary_flags) != len(p_values):
        raise ValueError("is_primary must be the same length as p_values")

    m = len(p_values)
    order = sorted(range(m), key=lambda i: p_values[i])
    q_values = [0.0] * m
    threshold_index = -1
    running_min = 1.0
    # Walk from the largest p-value down so each q-value is monotone
    # (never smaller than a less-significant comparison's q-value).
    for rank, index in reversed(list(enumerate(order, start=1))):
        candidate_q = p_values[index] * m / rank
        running_min = min(running_min, candidate_q)
        q_values[index] = running_min
        if p_values[index] <= (rank / m) * alpha:
            threshold_index = max(threshold_index, rank)

    significant_ranks = set(range(1, threshold_index + 1))
    rank_of_index = {index: rank for rank, index in enumerate(order, start=1)}

    return [
        FDRResult(
            p_value=p_values[i],
            q_value=q_values[i],
            significant=rank_of_index[i] in significant_ranks,
            label="confirmatory" if primary_flags[i] else "exploratory",
        )
        for i in range(m)
    ]


__all__ = ["FDRResult", "benjamini_hochberg"]
