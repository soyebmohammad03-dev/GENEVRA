"""A configurable 2D grid world: the first concrete `Environment`.

Deliberately not "solved" by one static policy: an organism must trade off
exploring for resources against the metabolic cost of moving (metabolism
lives in `genevra.organism.metabolism`, not here — this module only
implements world physics: terrain, resources, and stepping).
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

import numpy as np

from genevra.arrays import BoolArray, FloatArray
from genevra.simulation.dynamics import EnvironmentDynamics
from genevra.simulation.types import (
    Action,
    EnvironmentMetadata,
    Observation,
    Position,
    StepResult,
)

_ACTION_DELTAS: dict[Action, tuple[int, int]] = {
    Action.MOVE_NORTH: (0, -1),
    Action.MOVE_SOUTH: (0, 1),
    Action.MOVE_EAST: (1, 0),
    Action.MOVE_WEST: (-1, 0),
}


@dataclass(frozen=True)
class GridWorldConfig:
    """Validated, immutable configuration for a `GridWorld`.

    Densities/probabilities are per-cell-per-step (or per-cell-at-reset
    for `obstacle_density`/`resource_density`), not global counts, so
    behavior scales naturally with grid size.
    """

    width: int
    height: int
    view_radius: int = 1
    resource_density: float = 0.1
    resource_energy_value: float = 5.0
    resource_regen_prob: float = 0.01
    obstacle_density: float = 0.1
    max_steps: int = 500
    dynamics: EnvironmentDynamics | None = None
    """If given, overrides `resource_regen_prob` each step with
    `dynamics.regime_at(step, rng).resource_regen_prob` (see
    `genevra.simulation.dynamics`). `None` (the default) preserves the
    original fixed-`resource_regen_prob` behavior exactly — every caller
    from Phase 1-4 that never set this field is unaffected."""

    def __post_init__(self) -> None:
        if self.width < 3 or self.height < 3:
            raise ValueError("width and height must be >= 3")
        if self.view_radius < 0:
            raise ValueError("view_radius must be >= 0")
        for name, value in (
            ("resource_density", self.resource_density),
            ("resource_regen_prob", self.resource_regen_prob),
            ("obstacle_density", self.obstacle_density),
        ):
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"{name} must be in [0, 1], got {value}")
        if self.resource_energy_value <= 0:
            raise ValueError("resource_energy_value must be > 0")
        if self.max_steps <= 0:
            raise ValueError("max_steps must be > 0")


@dataclass(frozen=True, eq=False)
class GridWorldState:
    """A snapshot of everything the simulator knows that an organism must
    not: the full terrain/resource grids, absolute position, and RNG
    state. Used for checkpointing and deterministic replay only."""

    obstacles: BoolArray
    resources: FloatArray
    agent_position: Position
    step_count: int
    rng_state: Mapping[str, object]


class GridWorld:
    """A bounded (non-toroidal) 2D grid with obstacles and regenerating
    resources, sensed through a limited egocentric window."""

    def __init__(self, config: GridWorldConfig) -> None:
        self._config = config
        self._rng: np.random.Generator | None = None
        self._obstacles: BoolArray | None = None
        self._resources: FloatArray | None = None
        self._agent_position: Position | None = None
        self._step_count = 0

    def reset(self, seed: int | None = None) -> Observation:
        cfg = self._config
        self._rng = np.random.default_rng(seed)
        obstacles = self._rng.random((cfg.height, cfg.width)) < cfg.obstacle_density
        start = Position(cfg.width // 2, cfg.height // 2)
        obstacles[start.y, start.x] = False
        resource_sites = (~obstacles) & (
            self._rng.random((cfg.height, cfg.width)) < cfg.resource_density
        )
        resources = np.where(resource_sites, cfg.resource_energy_value, 0.0).astype(np.float32)
        resources[start.y, start.x] = 0.0

        self._obstacles = obstacles
        self._resources = resources
        self._agent_position = start
        self._step_count = 0
        return self.observe()

    def observe(self) -> Observation:
        self._require_reset()
        return Observation(local_grid=self._extract_local_grid())

    def step(self, action: Action) -> StepResult:
        self._require_reset()
        if not isinstance(action, Action):
            raise ValueError(f"invalid action: {action!r}")

        reward = 0.0
        if action in _ACTION_DELTAS:
            new_position = self._attempt_move(action)
            if new_position is not None:
                self._agent_position = new_position
        elif action is Action.EAT:
            reward = self._attempt_eat()

        self._regenerate_resources()
        self._step_count += 1
        done = self._step_count >= self._config.max_steps
        info = {"position": self._agent_position, "step_count": self._step_count}
        return StepResult(observation=self.observe(), reward=reward, done=done, info=info)

    def snapshot(self) -> GridWorldState:
        self._require_reset()
        assert self._rng is not None
        assert self._obstacles is not None
        assert self._resources is not None
        assert self._agent_position is not None
        return GridWorldState(
            obstacles=self._obstacles.copy(),
            resources=self._resources.copy(),
            agent_position=self._agent_position,
            step_count=self._step_count,
            rng_state=self._rng.bit_generator.state,
        )

    def restore(self, state: GridWorldState) -> None:
        self._obstacles = state.obstacles.copy()
        self._resources = state.resources.copy()
        self._agent_position = state.agent_position
        self._step_count = state.step_count
        self._rng = np.random.default_rng()
        self._rng.bit_generator.state = state.rng_state

    @property
    def metadata(self) -> EnvironmentMetadata:
        size = 2 * self._config.view_radius + 1
        return EnvironmentMetadata(
            width=self._config.width,
            height=self._config.height,
            action_space_size=len(Action),
            observation_shape=(size, size, 2),
            max_steps=self._config.max_steps,
        )

    def _require_reset(self) -> None:
        if self._agent_position is None:
            raise RuntimeError("GridWorld.reset() must be called before use")

    def _attempt_move(self, action: Action) -> Position | None:
        assert self._agent_position is not None
        assert self._obstacles is not None
        dx, dy = _ACTION_DELTAS[action]
        x, y = self._agent_position
        nx, ny = x + dx, y + dy
        if not (0 <= nx < self._config.width and 0 <= ny < self._config.height):
            return None
        if self._obstacles[ny, nx]:
            return None
        return Position(nx, ny)

    def _attempt_eat(self) -> float:
        assert self._agent_position is not None
        assert self._resources is not None
        x, y = self._agent_position
        amount = float(self._resources[y, x])
        if amount > 0:
            self._resources[y, x] = 0.0
        return amount

    def _regenerate_resources(self) -> None:
        assert self._rng is not None
        assert self._obstacles is not None
        assert self._resources is not None
        cfg = self._config
        regen_prob = (
            cfg.dynamics.regime_at(self._step_count, self._rng).resource_regen_prob
            if cfg.dynamics is not None
            else cfg.resource_regen_prob
        )
        empty = (~self._obstacles) & (self._resources == 0.0)
        spawn = empty & (self._rng.random(self._resources.shape) < regen_prob)
        self._resources[spawn] = cfg.resource_energy_value

    def _extract_local_grid(self) -> FloatArray:
        assert self._agent_position is not None
        assert self._obstacles is not None
        assert self._resources is not None
        r = self._config.view_radius
        x, y = self._agent_position
        window_obstacles, window_resources = extract_local_window(
            self._obstacles,
            self._resources,
            x,
            y,
            r,
            self._config.width,
            self._config.height,
        )
        normalized = window_resources / self._config.resource_energy_value
        grid: FloatArray = np.stack(
            [window_obstacles.astype(np.float32), normalized.astype(np.float32)], axis=-1
        )
        return grid


def _window_bounds(x: int, y: int, r: int, width: int, height: int) -> tuple[int, ...]:
    src_x0, src_x1 = max(0, x - r), min(width, x + r + 1)
    src_y0, src_y1 = max(0, y - r), min(height, y + r + 1)
    dst_x0, dst_y0 = src_x0 - (x - r), src_y0 - (y - r)
    dst_x1, dst_y1 = dst_x0 + max(0, src_x1 - src_x0), dst_y0 + max(0, src_y1 - src_y0)
    return src_x0, src_x1, src_y0, src_y1, dst_x0, dst_x1, dst_y0, dst_y1


def extract_single_window(
    array: np.ndarray, fill_value: object, x: int, y: int, r: int, width: int, height: int
) -> np.ndarray:
    """Bounds-aware slicing extraction of one `(2r+1, 2r+1)` egocentric
    window from `array`, equivalent to padding the whole grid with
    `fill_value` and slicing out the window — but touching only the (at
    most) `(2r+1)^2` window cells rather than allocating and filling a
    padded copy of the entire `width x height` grid on every call. See
    `tests/test_grid_world.py` for equivalence tests against a reference
    `np.pad`-based implementation across randomized positions, sizes,
    radii, and boundary conditions.
    """
    size = 2 * r + 1
    window = np.full((size, size), fill_value, dtype=array.dtype)
    src_x0, src_x1, src_y0, src_y1, dst_x0, dst_x1, dst_y0, dst_y1 = _window_bounds(
        x, y, r, width, height
    )
    if src_x0 < src_x1 and src_y0 < src_y1:
        window[dst_y0:dst_y1, dst_x0:dst_x1] = array[src_y0:src_y1, src_x0:src_x1]
    return window


def extract_local_window(
    obstacles: BoolArray,
    resources: FloatArray,
    x: int,
    y: int,
    r: int,
    width: int,
    height: int,
) -> tuple[BoolArray, FloatArray]:
    """`GridWorld`'s two-channel case: obstacle window (out-of-bounds =
    wall) and resource window (out-of-bounds = no resource)."""
    window_obstacles = extract_single_window(obstacles, True, x, y, r, width, height)
    window_resources = extract_single_window(resources, 0.0, x, y, r, width, height)
    return window_obstacles, window_resources
