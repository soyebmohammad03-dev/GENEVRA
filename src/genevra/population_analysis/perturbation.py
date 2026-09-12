"""Phase 16.9: controlled ecological perturbation experiments.

Runs a `ContinuousEvolutionEngine` through three windows — before,
during, after — applying a caller-supplied perturbation function only
during the middle window (e.g. `SharedGridWorld.perturb_resources`).
`resistance` (how much a metric dropped when the perturbation hit) and
`recovery` (whether/how fast it returned to near its pre-perturbation
level during the after-window) are reported as two separate quantities,
per Phase 16.9's explicit requirement — a metric can resist without
recovering, or recover slowly after not resisting at all, and collapsing
those into one number would hide which happened.
"""

from __future__ import annotations

import dataclasses
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

import numpy as np

from genevra.evolution.continuous import ContinuousEvolutionEngine


@dataclass(frozen=True)
class PerturbationWindowResult:
    before_values: tuple[float, ...]
    during_values: tuple[float, ...]
    after_values: tuple[float, ...]
    resistance: float | None
    """`mean(before) - min(during)` for a metric where lower during the
    perturbation is worse (e.g. population size, diversity). `None` if
    either window has no data."""
    recovered: bool | None
    """Whether the after-window's final value came back within 10% of
    the before-window's mean. `None` if either window has no data."""
    recovery_step_index: int | None
    """Index (0-based) into `after_values` of the first value that met
    the recovery threshold, or `None` if it never did."""

    def to_dict(self) -> dict[str, Any]:
        return dataclasses.asdict(self)


def evaluate_perturbation_windows(
    before: list[float], during: list[float], after: list[float], recovery_tolerance: float = 0.1
) -> PerturbationWindowResult:
    if not before or not during:
        return PerturbationWindowResult(
            tuple(before), tuple(during), tuple(after), None, None, None
        )
    baseline = float(np.mean(before))
    resistance = baseline - min(during)
    if not after:
        return PerturbationWindowResult(
            tuple(before), tuple(during), tuple(after), resistance, None, None
        )
    threshold = baseline * (1.0 - recovery_tolerance)
    recovery_index = next((i for i, v in enumerate(after) if v >= threshold), None)
    return PerturbationWindowResult(
        tuple(before),
        tuple(during),
        tuple(after),
        resistance,
        recovery_index is not None,
        recovery_index,
    )


def run_perturbation_experiment(
    engine: ContinuousEvolutionEngine,
    before_steps: int,
    during_steps: int,
    after_steps: int,
    apply_perturbation: Callable[[ContinuousEvolutionEngine], None],
    metric: Callable[[ContinuousEvolutionEngine], float],
) -> PerturbationWindowResult:
    """Runs `engine` for `before_steps`, calls `apply_perturbation` once,
    runs `during_steps` more, then `after_steps` more, recording
    `metric(engine)` once per step in each window. `engine` must already
    be initialized (`engine.initialize()` called) or have
    `engine.population` non-empty."""
    if not engine.population:
        engine.initialize()

    def run_window(n: int) -> list[float]:
        values = []
        for _ in range(n):
            engine.step()
            values.append(metric(engine))
        return values

    before = run_window(before_steps)
    apply_perturbation(engine)
    during = run_window(during_steps)
    after = run_window(after_steps)
    return evaluate_perturbation_windows(before, during, after)


__all__ = [
    "PerturbationWindowResult",
    "evaluate_perturbation_windows",
    "run_perturbation_experiment",
]
