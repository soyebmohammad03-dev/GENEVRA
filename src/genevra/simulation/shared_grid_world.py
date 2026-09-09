"""A shared ecological world: multiple organisms coexisting in one
environment instance, competing for two resource types, under
configurable temporal dynamics.

This is deliberately a *separate* class from `GridWorld`, not a
modification of it — `GridWorld`'s one-organism-per-episode mode remains
byte-for-byte what Phase 1/2 built and is a valid experimental condition
in its own right (see `docs/ecology.md` for why isolated vs. shared
episodes are both legitimate, comparable conditions rather than one being
a strict upgrade of the other).

The same information-boundary discipline as `GridWorld` applies: each
agent's `Observation` is an egocentric local window (now three channels —
obstacle, resource A, resource B); absolute positions, the full grid, and
RNG state are simulator-internal, reachable only via `snapshot()`/
`restore()`.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field

import numpy as np

from genevra.arrays import BoolArray, FloatArray
from genevra.simulation.dynamics import EnvironmentDynamics, EnvironmentRegime, StaticDynamics
from genevra.simulation.interaction import InteractionSystem, SpatialCompetition
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
class SharedGridWorldConfig:
    width: int
    height: int
    view_radius: int = 1
    max_agents: int = 20
    obstacle_density: float = 0.1
    resource_a_density: float = 0.15
    resource_a_value: float = 3.0
    resource_b_density: float = 0.05
    resource_b_value: float = 10.0
    dynamics: EnvironmentDynamics = field(
        default_factory=lambda: StaticDynamics(EnvironmentRegime(resource_regen_prob=0.02))
    )
    max_steps: int = 500

    def __post_init__(self) -> None:
        if self.width < 3 or self.height < 3:
            raise ValueError("width and height must be >= 3")
        if self.view_radius < 0:
            raise ValueError("view_radius must be >= 0")
        if self.max_agents <= 0:
            raise ValueError("max_agents must be positive")
        for name, value in (
            ("obstacle_density", self.obstacle_density),
            ("resource_a_density", self.resource_a_density),
            ("resource_b_density", self.resource_b_density),
        ):
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"{name} must be in [0, 1], got {value}")
        if self.resource_a_value <= 0 or self.resource_b_value <= 0:
            raise ValueError("resource values must be > 0")
        if self.max_steps <= 0:
            raise ValueError("max_steps must be > 0")


@dataclass(frozen=True, eq=False)
class SharedGridWorldState:
    """Simulator-internal snapshot: full grids, every agent's absolute
    position, step count, and RNG state. Never handed to an organism."""

    obstacles: BoolArray
    resources_a: FloatArray
    resources_b: FloatArray
    agent_positions: dict[int, Position]
    step_count: int
    rng_state: Mapping[str, object]


class SharedGridWorld:
    def __init__(
        self, config: SharedGridWorldConfig, interaction_system: InteractionSystem | None = None
    ) -> None:
        self._config = config
        self._interaction = (
            interaction_system if interaction_system is not None else SpatialCompetition()
        )
        self._rng: np.random.Generator | None = None
        self._obstacles: BoolArray | None = None
        self._resources_a: FloatArray | None = None
        self._resources_b: FloatArray | None = None
        self._agent_positions: dict[int, Position] = {}
        self._step_count = 0
        self._interaction_events = 0

    def reset(self, seed: int) -> None:
        cfg = self._config
        self._rng = np.random.default_rng(seed)
        obstacles = self._rng.random((cfg.height, cfg.width)) < cfg.obstacle_density
        free = ~obstacles

        a_sites = free & (self._rng.random((cfg.height, cfg.width)) < cfg.resource_a_density)
        remaining_free = free & ~a_sites
        b_sites = remaining_free & (
            self._rng.random((cfg.height, cfg.width)) < cfg.resource_b_density
        )

        self._obstacles = obstacles
        self._resources_a = np.where(a_sites, cfg.resource_a_value, 0.0).astype(np.float32)
        self._resources_b = np.where(b_sites, cfg.resource_b_value, 0.0).astype(np.float32)
        self._agent_positions = {}
        self._step_count = 0
        self._interaction_events = 0

    def add_agent(self, agent_id: int) -> Observation:
        self._require_reset()
        if agent_id in self._agent_positions:
            raise ValueError(f"agent {agent_id} is already present")
        if len(self._agent_positions) >= self._config.max_agents:
            raise RuntimeError("world is at max_agents capacity")
        position = self._find_free_cell()
        self._agent_positions[agent_id] = position
        return self.observe(agent_id)

    def remove_agent(self, agent_id: int) -> None:
        self._agent_positions.pop(agent_id, None)

    def observe(self, agent_id: int) -> Observation:
        self._require_reset()
        if agent_id not in self._agent_positions:
            raise ValueError(f"agent {agent_id} is not present")
        return Observation(local_grid=self._extract_local_grid(self._agent_positions[agent_id]))

    @property
    def agent_ids(self) -> list[int]:
        return list(self._agent_positions)

    def step(self, actions: Mapping[int, Action]) -> dict[int, StepResult]:
        self._require_reset()
        assert self._obstacles is not None
        assert self._rng is not None
        for agent_id, action in actions.items():
            if agent_id not in self._agent_positions:
                raise ValueError(f"agent {agent_id} is not present")
            if not isinstance(action, Action):
                raise ValueError(f"invalid action for agent {agent_id}: {action!r}")

        desired = {
            agent_id: self._intended_position(self._agent_positions[agent_id], action)
            for agent_id, action in actions.items()
        }
        resolved = self._interaction.resolve_movements(
            dict(self._agent_positions),
            desired,
            self._obstacles,
            self._config.width,
            self._config.height,
        )
        for agent_id, action in actions.items():
            if (
                action not in _ACTION_DELTAS
                or resolved[agent_id] != self._agent_positions[agent_id]
            ):
                continue  # not a move attempt, or it succeeded
            target = desired[agent_id]
            in_bounds = 0 <= target.x < self._config.width and 0 <= target.y < self._config.height
            if in_bounds and not self._obstacles[target.y, target.x]:
                self._interaction_events += 1  # blocked by another agent, not terrain
        self._agent_positions.update(resolved)

        rewards: dict[int, float] = dict.fromkeys(actions, 0.0)
        for agent_id, action in actions.items():
            if action is Action.EAT:
                rewards[agent_id] = self._attempt_eat(self._agent_positions[agent_id])

        self._regenerate_resources()
        self._step_count += 1
        done = self._step_count >= self._config.max_steps

        results: dict[int, StepResult] = {}
        for agent_id in actions:
            position = self._agent_positions[agent_id]
            results[agent_id] = StepResult(
                observation=self.observe(agent_id),
                reward=rewards[agent_id],
                done=done,
                info={"position": position, "step_count": self._step_count},
            )
        return results

    def snapshot(self) -> SharedGridWorldState:
        self._require_reset()
        assert self._rng is not None
        assert self._obstacles is not None
        assert self._resources_a is not None
        assert self._resources_b is not None
        return SharedGridWorldState(
            obstacles=self._obstacles.copy(),
            resources_a=self._resources_a.copy(),
            resources_b=self._resources_b.copy(),
            agent_positions=dict(self._agent_positions),
            step_count=self._step_count,
            rng_state=self._rng.bit_generator.state,
        )

    def restore(self, state: SharedGridWorldState) -> None:
        self._obstacles = state.obstacles.copy()
        self._resources_a = state.resources_a.copy()
        self._resources_b = state.resources_b.copy()
        self._agent_positions = dict(state.agent_positions)
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
            observation_shape=(size, size, 3),
            max_steps=self._config.max_steps,
        )

    @property
    def interaction_events(self) -> int:
        """Count of movement attempts blocked by another agent (not by an
        obstacle or a boundary) since the last `reset()` — GENEVRA's
        minimal organism-organism interaction counter."""
        return self._interaction_events

    def _require_reset(self) -> None:
        if self._obstacles is None:
            raise RuntimeError("SharedGridWorld.reset() must be called before use")

    def _find_free_cell(self) -> Position:
        assert self._obstacles is not None
        assert self._rng is not None
        cfg = self._config
        occupied = set(self._agent_positions.values())
        for _ in range(cfg.width * cfg.height * 4):
            x = int(self._rng.integers(0, cfg.width))
            y = int(self._rng.integers(0, cfg.height))
            candidate = Position(x, y)
            if not self._obstacles[y, x] and candidate not in occupied:
                return candidate
        raise RuntimeError("no free cell available to place a new agent")

    def _intended_position(self, current: Position, action: Action) -> Position:
        if action not in _ACTION_DELTAS:
            return current
        dx, dy = _ACTION_DELTAS[action]
        return Position(current.x + dx, current.y + dy)

    def _attempt_eat(self, position: Position) -> float:
        assert self._resources_a is not None
        assert self._resources_b is not None
        x, y = position
        amount_a = float(self._resources_a[y, x])
        if amount_a > 0:
            self._resources_a[y, x] = 0.0
            return amount_a
        amount_b = float(self._resources_b[y, x])
        if amount_b > 0:
            self._resources_b[y, x] = 0.0
            return amount_b
        return 0.0

    def _regenerate_resources(self) -> None:
        assert self._rng is not None
        assert self._obstacles is not None
        assert self._resources_a is not None
        assert self._resources_b is not None
        cfg = self._config
        regime = cfg.dynamics.regime_at(self._step_count, self._rng)
        empty = (~self._obstacles) & (self._resources_a == 0.0) & (self._resources_b == 0.0)

        spawn_a = empty & (
            self._rng.random(self._resources_a.shape) < regime.resource_regen_prob * 0.75
        )
        self._resources_a[spawn_a] = cfg.resource_a_value

        still_empty = empty & ~spawn_a
        spawn_b = still_empty & (
            self._rng.random(self._resources_b.shape) < regime.resource_regen_prob * 0.25
        )
        self._resources_b[spawn_b] = cfg.resource_b_value

    def _extract_local_grid(self, position: Position) -> FloatArray:
        assert self._obstacles is not None
        assert self._resources_a is not None
        assert self._resources_b is not None
        r = self._config.view_radius
        x, y = position
        obstacles_padded = np.pad(self._obstacles, r, mode="constant", constant_values=True)
        a_padded = np.pad(self._resources_a, r, mode="constant", constant_values=0.0)
        b_padded = np.pad(self._resources_b, r, mode="constant", constant_values=0.0)
        window = (slice(y, y + 2 * r + 1), slice(x, x + 2 * r + 1))
        grid: FloatArray = np.stack(
            [
                obstacles_padded[window].astype(np.float32),
                (a_padded[window] / self._config.resource_a_value).astype(np.float32),
                (b_padded[window] / self._config.resource_b_value).astype(np.float32),
            ],
            axis=-1,
        )
        return grid
