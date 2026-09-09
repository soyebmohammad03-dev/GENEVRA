import numpy as np
import pytest

from genevra.simulation.grid_world import GridWorld, GridWorldConfig
from genevra.simulation.types import Action


def make_world(**overrides: object) -> GridWorld:
    defaults: dict[str, object] = dict(
        width=9,
        height=9,
        view_radius=1,
        resource_density=0.2,
        resource_energy_value=5.0,
        resource_regen_prob=0.05,
        obstacle_density=0.15,
        max_steps=50,
    )
    defaults.update(overrides)
    return GridWorld(GridWorldConfig(**defaults))  # type: ignore[arg-type]


def test_config_rejects_invalid_values() -> None:
    with pytest.raises(ValueError):
        GridWorldConfig(width=1, height=9)
    with pytest.raises(ValueError):
        GridWorldConfig(width=9, height=9, resource_density=1.5)
    with pytest.raises(ValueError):
        GridWorldConfig(width=9, height=9, max_steps=0)


def test_reset_returns_observation_with_expected_shape() -> None:
    world = make_world(view_radius=2)
    obs = world.reset(seed=1)
    assert obs.local_grid.shape == (5, 5, 2)
    assert world.metadata.observation_shape == (5, 5, 2)


def test_same_seed_is_fully_deterministic() -> None:
    world_a = make_world()
    world_b = make_world()
    obs_a = world_a.reset(seed=42)
    obs_b = world_b.reset(seed=42)
    assert np.array_equal(obs_a.local_grid, obs_b.local_grid)

    actions = [Action.MOVE_EAST, Action.MOVE_SOUTH, Action.STAY, Action.EAT, Action.MOVE_NORTH]
    for action in actions:
        result_a = world_a.step(action)
        result_b = world_b.step(action)
        assert np.array_equal(result_a.observation.local_grid, result_b.observation.local_grid)
        assert result_a.reward == result_b.reward
        assert result_a.done == result_b.done
        assert result_a.info["position"] == result_b.info["position"]


def test_different_seeds_can_diverge() -> None:
    world_a = make_world(obstacle_density=0.3, resource_density=0.3)
    world_b = make_world(obstacle_density=0.3, resource_density=0.3)
    world_a.reset(seed=1)
    world_b.reset(seed=2)
    diverged = False
    for _ in range(20):
        result_a = world_a.step(Action.MOVE_EAST)
        result_b = world_b.step(Action.MOVE_EAST)
        if not np.array_equal(result_a.observation.local_grid, result_b.observation.local_grid):
            diverged = True
            break
    assert diverged


def test_observe_before_reset_raises() -> None:
    world = make_world()
    with pytest.raises(RuntimeError):
        world.observe()


def test_invalid_action_raises() -> None:
    world = make_world()
    world.reset(seed=0)
    with pytest.raises(ValueError):
        world.step(99)  # type: ignore[arg-type]


def test_boundary_movement_is_a_no_op_not_a_crash() -> None:
    world = make_world(width=3, height=3, obstacle_density=0.0)
    world.reset(seed=0)
    # Start is the center of a 3x3 grid; walk off the north-west corner
    # repeatedly and confirm the agent never leaves the grid.
    for action in [Action.MOVE_NORTH, Action.MOVE_WEST] * 5:
        result = world.step(action)
        x, y = result.info["position"]
        assert 0 <= x < 3
        assert 0 <= y < 3


def test_eat_consumes_resource_and_grants_reward() -> None:
    world = make_world(
        width=5, height=5, obstacle_density=0.0, resource_density=0.0, resource_regen_prob=0.0
    )
    world.reset(seed=0)
    snapshot = world.snapshot()
    cx, cy = snapshot.agent_position
    # Manually place a resource under the agent via a restored snapshot.
    resources = snapshot.resources.copy()
    resources[cy, cx] = snapshot_resource_value = 5.0
    from genevra.simulation.grid_world import GridWorldState

    restored = GridWorldState(
        obstacles=snapshot.obstacles,
        resources=resources,
        agent_position=snapshot.agent_position,
        step_count=snapshot.step_count,
        rng_state=snapshot.rng_state,
    )
    world.restore(restored)

    result = world.step(Action.EAT)
    assert result.reward == snapshot_resource_value

    result_again = world.step(Action.EAT)
    assert result_again.reward == 0.0


def test_resources_regenerate_over_time() -> None:
    world = make_world(
        width=6, height=6, obstacle_density=0.0, resource_density=0.0, resource_regen_prob=1.0
    )
    world.reset(seed=0)
    total_resource_signal = 0.0
    for _ in range(5):
        result = world.step(Action.STAY)
        total_resource_signal += float(result.observation.local_grid[..., 1].sum())
    assert total_resource_signal > 0.0


def test_snapshot_restore_round_trips_state() -> None:
    world = make_world()
    world.reset(seed=7)
    for _ in range(5):
        world.step(Action.MOVE_EAST)
    snapshot = world.snapshot()

    for _ in range(5):
        world.step(Action.MOVE_SOUTH)
    world.restore(snapshot)

    replay_result = world.step(Action.MOVE_NORTH)

    world_b = make_world()
    world_b.reset(seed=7)
    for _ in range(5):
        world_b.step(Action.MOVE_EAST)
    expected_result = world_b.step(Action.MOVE_NORTH)

    assert np.array_equal(
        replay_result.observation.local_grid, expected_result.observation.local_grid
    )
    assert replay_result.info["position"] == expected_result.info["position"]


def test_max_steps_triggers_done() -> None:
    world = make_world(max_steps=3)
    world.reset(seed=0)
    result = world.step(Action.STAY)
    assert not result.done
    result = world.step(Action.STAY)
    assert not result.done
    result = world.step(Action.STAY)
    assert result.done
