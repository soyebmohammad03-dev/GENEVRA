"""The `Environment` protocol and a loop-based batch wrapper around it.

Any environment (GridWorld today; future variants with hazards, multiple
resource types, other organisms, ...) implements this structural interface
so that organism/evolution code depends on the protocol, never on a
concrete environment class.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any, Protocol, runtime_checkable

from genevra.simulation.types import Action, EnvironmentMetadata, Observation, StepResult


@runtime_checkable
class Environment(Protocol):
    """Lifecycle: `reset(seed)` -> repeated `step(action)` -> episode end.

    `observe()` is idempotent and side-effect free, so callers can inspect
    the current observation without advancing simulation time.
    `snapshot()`/`restore()` expose simulator-internal state for
    checkpointing and deterministic replay; that state is opaque to
    organisms and intentionally not part of this protocol's return types
    for `reset`/`observe`/`step`.
    """

    def reset(self, seed: int | None = None) -> Observation: ...

    def observe(self) -> Observation: ...

    def step(self, action: Action) -> StepResult: ...

    def snapshot(self) -> Any: ...

    def restore(self, state: Any) -> None: ...

    @property
    def metadata(self) -> EnvironmentMetadata: ...


class VectorEnvironment:
    """A batch of independent `Environment` instances, stepped together.

    ponytail: this loops over instances rather than fusing them into
    shared NumPy operations across environments — correct and simple, and
    fast enough for the organism counts a laptop can run one-at-a-time.
    Fuse into batched array ops if profiling later shows this loop is the
    bottleneck.
    """

    def __init__(self, envs: Sequence[Environment]) -> None:
        self._envs: list[Environment] = list(envs)

    def __len__(self) -> int:
        return len(self._envs)

    def reset(self, seeds: Sequence[int | None]) -> list[Observation]:
        return [env.reset(seed) for env, seed in zip(self._envs, seeds, strict=True)]

    def step(self, actions: Sequence[Action]) -> list[StepResult]:
        return [env.step(action) for env, action in zip(self._envs, actions, strict=True)]
