"""Phase 10.10: detects when two experiments' correlation results point
in opposite directions for the same variable pair. Never resolves the
disagreement automatically — the resolution is exactly what a
replication run (`genevra.discovery.replication`) or a closer look at
differing conditions is for.
"""

from __future__ import annotations

import itertools
from collections.abc import Sequence
from dataclasses import dataclass

from genevra.discovery.correlation import CorrelationResult


@dataclass(frozen=True)
class Contradiction:
    variable_a: str
    variable_b: str
    experiment_a: str
    experiment_b: str
    rho_a: float
    rho_b: float
    n_runs_a: int
    n_runs_b: int
    replication_needed: bool = True
    note: str = (
        "Two experiments report opposite-signed correlations for the same variable "
        "pair. This is not automatically resolved: it may reflect differing "
        "conditions, a confound, or insufficient seeds in one or both experiments. "
        "Treat as a candidate for replication, not a settled disagreement."
    )


@dataclass(frozen=True)
class ExperimentCorrelation:
    """One experiment's `CorrelationResult` for a variable pair — the
    unit `find_contradictions` compares across experiments."""

    experiment: str
    result: CorrelationResult


def find_contradictions(
    experiment_results: Sequence[ExperimentCorrelation],
    effect_size_threshold: float = 0.2,
) -> list[Contradiction]:
    """Groups results by `(variable_a, variable_b)`, then flags any pair
    of experiments within a group whose Spearman rho signs disagree and
    whose magnitudes both clear `effect_size_threshold` — a small,
    noisy rho near zero on either side is not treated as a real
    disagreement."""
    by_pair: dict[tuple[str, str], list[ExperimentCorrelation]] = {}
    for item in experiment_results:
        key = (item.result.variable_a, item.result.variable_b)
        by_pair.setdefault(key, []).append(item)

    contradictions = []
    for (variable_a, variable_b), items in by_pair.items():
        for left, right in itertools.combinations(items, 2):
            rho_left, rho_right = left.result.spearman_rho, right.result.spearman_rho
            if (
                abs(rho_left) < effect_size_threshold
                or abs(rho_right) < effect_size_threshold
                or (rho_left > 0) == (rho_right > 0)
            ):
                continue
            contradictions.append(
                Contradiction(
                    variable_a=variable_a,
                    variable_b=variable_b,
                    experiment_a=left.experiment,
                    experiment_b=right.experiment,
                    rho_a=rho_left,
                    rho_b=rho_right,
                    n_runs_a=left.result.n_runs,
                    n_runs_b=right.result.n_runs,
                )
            )
    return contradictions


__all__ = ["Contradiction", "ExperimentCorrelation", "find_contradictions"]
