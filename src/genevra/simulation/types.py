"""Core typed data structures shared by every environment implementation."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from enum import IntEnum
from typing import Any, NamedTuple

from genevra.arrays import FloatArray


class Position(NamedTuple):
    """Integer grid coordinates. Simulator/organism-internal bookkeeping
    only — never handed to an organism directly (see `Observation`)."""

    x: int
    y: int


class Action(IntEnum):
    """The shared discrete action space. EAT is a distinct action (rather
    than auto-consuming resources on arrival) so that resource acquisition
    is a decision an organism must sense and choose, not a free side
    effect of movement."""

    STAY = 0
    MOVE_NORTH = 1
    MOVE_SOUTH = 2
    MOVE_EAST = 3
    MOVE_WEST = 4
    EAT = 5


@dataclass(frozen=True, eq=False)
class Observation:
    """Everything an organism can sense from the environment this step.

    `local_grid` has shape `(2*radius+1, 2*radius+1, 2)`: channel 0 is
    1.0 for obstacle/out-of-bounds and 0.0 for free space; channel 1 is
    the resource amount at that cell, normalized to `[0, 1]`. This is
    strictly an egocentric, radius-limited window — no absolute position,
    no global grid, no other organisms' state. Anything not derivable from
    this object is not information the organism is allowed to have.
    """

    local_grid: FloatArray


@dataclass(frozen=True, eq=False)
class StepResult:
    """Result of one environment step.

    `reward` is a world-physics signal only (resource energy made
    available this step) — it is not an organism's fitness or energy
    budget, which are metabolism concerns (see `genevra.organism.metabolism`).
    `info` is simulator-only diagnostic metadata (e.g. absolute position)
    for logging/tests/replay; it must never be fed into an organism's
    controller.
    """

    observation: Observation
    reward: float
    done: bool
    info: Mapping[str, Any]


@dataclass(frozen=True)
class EnvironmentMetadata:
    """Static shape/size information about an environment instance."""

    width: int
    height: int
    action_space_size: int
    observation_shape: tuple[int, ...]
    max_steps: int
