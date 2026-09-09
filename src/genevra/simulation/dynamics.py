"""Temporal environment dynamics: how an environment's resource
regeneration rate changes over the course of a run.

`EnvironmentDynamics.regime_at(step, rng)` is consulted once per
environment step and returns the `EnvironmentRegime` in force at that
step — environments never mutate their own dynamics; they only ask what
regime applies now. Four modes are provided: `StaticDynamics` (no change —
the existing single-regime behavior), `PeriodicDynamics` (a deterministic
two-regime cycle), `RegimeChangeDynamics` (a one-time deterministic
switch), and `StochasticDynamics` (bounded random perturbation using the
environment's own seeded RNG, so it stays reproducible). All four are
plain, reproducible functions of `(step, rng)` — environmental change is
therefore configurable, observable only through what organisms can sense
(resource availability), and independent of organism internals.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

import numpy as np


@dataclass(frozen=True)
class EnvironmentRegime:
    resource_regen_prob: float

    def __post_init__(self) -> None:
        if not 0.0 <= self.resource_regen_prob <= 1.0:
            raise ValueError("resource_regen_prob must be in [0, 1]")


class EnvironmentDynamics(Protocol):
    def regime_at(self, step: int, rng: np.random.Generator) -> EnvironmentRegime: ...


@dataclass(frozen=True)
class StaticDynamics:
    regime: EnvironmentRegime

    def regime_at(self, step: int, rng: np.random.Generator) -> EnvironmentRegime:
        return self.regime


@dataclass(frozen=True)
class PeriodicDynamics:
    """A deterministic square-wave cycle: regime `a` for the first half of
    each `period`-step window, regime `b` for the second half."""

    regime_a: EnvironmentRegime
    regime_b: EnvironmentRegime
    period: int

    def __post_init__(self) -> None:
        if self.period <= 0:
            raise ValueError("period must be positive")

    def regime_at(self, step: int, rng: np.random.Generator) -> EnvironmentRegime:
        return self.regime_a if (step % self.period) < self.period // 2 else self.regime_b


@dataclass(frozen=True)
class RegimeChangeDynamics:
    """A single deterministic switch from one regime to another at
    `switch_step`."""

    regime_before: EnvironmentRegime
    regime_after: EnvironmentRegime
    switch_step: int

    def __post_init__(self) -> None:
        if self.switch_step < 0:
            raise ValueError("switch_step must be >= 0")

    def regime_at(self, step: int, rng: np.random.Generator) -> EnvironmentRegime:
        return self.regime_before if step < self.switch_step else self.regime_after


@dataclass(frozen=True)
class StochasticDynamics:
    """`resource_regen_prob` perturbed each step by
    `Normal(0, regen_prob_std)`, clipped to `[0, 1]`, drawn from the
    caller-supplied RNG — typically the environment's own seeded
    generator, so this stays fully reproducible from a seed despite being
    stochastic."""

    base_regime: EnvironmentRegime
    regen_prob_std: float

    def __post_init__(self) -> None:
        if self.regen_prob_std < 0:
            raise ValueError("regen_prob_std must be >= 0")

    def regime_at(self, step: int, rng: np.random.Generator) -> EnvironmentRegime:
        perturbed = float(
            np.clip(rng.normal(self.base_regime.resource_regen_prob, self.regen_prob_std), 0.0, 1.0)
        )
        return EnvironmentRegime(resource_regen_prob=perturbed)
