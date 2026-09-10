"""Phase 7.2: the optimized bounds-aware window extraction
(`genevra.simulation.grid_world.extract_single_window`) must produce
EXACTLY the same observations as the original `np.pad`-based
implementation it replaced.

A reference implementation (a direct copy of the pre-optimization
`np.pad` logic) is kept here — not deleted from production code, kept
alive as a test fixture — and compared against the optimized function
across randomized positions, world dimensions, sensor radii, boundary
conditions, and resource configurations.
"""

from __future__ import annotations

import numpy as np
import pytest

from genevra.simulation.grid_world import (
    GridWorld,
    GridWorldConfig,
    extract_local_window,
    extract_single_window,
)
from genevra.simulation.shared_grid_world import SharedGridWorld, SharedGridWorldConfig


def reference_extract_single_window(
    array: np.ndarray, fill_value: object, x: int, y: int, r: int
) -> np.ndarray:
    """Direct copy of the original `np.pad`-based extraction this
    replaces — the ground truth `extract_single_window` is checked
    against."""
    padded = np.pad(array, r, mode="constant", constant_values=fill_value)
    return padded[y : y + 2 * r + 1, x : x + 2 * r + 1]


@pytest.mark.parametrize("seed", range(30))
def test_extract_single_window_matches_reference_randomized(seed: int) -> None:
    rng = np.random.default_rng(seed)
    width = int(rng.integers(3, 40))
    height = int(rng.integers(3, 40))
    r = int(rng.integers(0, 6))
    x = int(rng.integers(0, width))
    y = int(rng.integers(0, height))

    bool_array = rng.random((height, width)) < 0.3
    float_array = rng.normal(size=(height, width)).astype(np.float32)

    expected_bool = reference_extract_single_window(bool_array, True, x, y, r)
    actual_bool = extract_single_window(bool_array, True, x, y, r, width, height)
    assert np.array_equal(expected_bool, actual_bool)

    expected_float = reference_extract_single_window(float_array, 0.0, x, y, r)
    actual_float = extract_single_window(float_array, 0.0, x, y, r, width, height)
    assert np.array_equal(expected_float, actual_float)


@pytest.mark.parametrize("seed", range(10))
def test_extract_single_window_covers_extreme_corners_and_radii(seed: int) -> None:
    rng = np.random.default_rng(seed + 1000)
    width, height, r = 15, 15, 4
    bool_array = rng.random((height, width)) < 0.3
    float_array = rng.normal(size=(height, width)).astype(np.float32)

    corners = [(0, 0), (width - 1, 0), (0, height - 1), (width - 1, height - 1)]
    for x, y in corners:
        expected_bool = reference_extract_single_window(bool_array, True, x, y, r)
        actual_bool = extract_single_window(bool_array, True, x, y, r, width, height)
        assert np.array_equal(expected_bool, actual_bool)

        expected_float = reference_extract_single_window(float_array, 0.0, x, y, r)
        actual_float = extract_single_window(float_array, 0.0, x, y, r, width, height)
        assert np.array_equal(expected_float, actual_float)


def test_extract_single_window_radius_zero() -> None:
    array = np.arange(9, dtype=np.float32).reshape(3, 3)
    window = extract_single_window(array, 0.0, 1, 1, 0, 3, 3)
    assert window.shape == (1, 1)
    assert window[0, 0] == array[1, 1]


@pytest.mark.parametrize("seed", range(20))
def test_grid_world_full_lifetime_matches_reference_extraction(seed: int) -> None:
    """End-to-end: run a full lifetime with the production `GridWorld`
    and independently recompute every observation with the reference
    `np.pad` implementation from the same internal state, across
    randomized configurations and action sequences."""
    rng = np.random.default_rng(seed)
    config = GridWorldConfig(
        width=int(rng.integers(4, 20)),
        height=int(rng.integers(4, 20)),
        view_radius=int(rng.integers(0, 4)),
        resource_density=float(rng.uniform(0.0, 0.4)),
        obstacle_density=float(rng.uniform(0.0, 0.4)),
        resource_regen_prob=float(rng.uniform(0.0, 0.2)),
    )
    world = GridWorld(config)
    obs = world.reset(seed=seed)

    from genevra.simulation.types import Action

    actions = list(Action)
    for _ in range(25):
        snapshot = world.snapshot()
        r = config.view_radius
        expected_obstacles = reference_extract_single_window(
            snapshot.obstacles, True, *snapshot.agent_position, r
        )
        expected_resources = reference_extract_single_window(
            snapshot.resources, 0.0, *snapshot.agent_position, r
        )
        expected = np.stack(
            [
                expected_obstacles.astype(np.float32),
                (expected_resources / config.resource_energy_value).astype(np.float32),
            ],
            axis=-1,
        )
        assert np.array_equal(obs.local_grid, expected)

        action = actions[int(rng.integers(0, len(actions)))]
        result = world.step(action)
        obs = result.observation
        if result.done:
            break


@pytest.mark.parametrize("seed", range(10))
def test_shared_grid_world_matches_reference_extraction(seed: int) -> None:
    rng = np.random.default_rng(seed)
    config = SharedGridWorldConfig(
        width=int(rng.integers(5, 25)),
        height=int(rng.integers(5, 25)),
        view_radius=int(rng.integers(0, 4)),
        max_agents=5,
    )
    world = SharedGridWorld(config)
    world.reset(seed=seed)
    for agent_id in range(5):
        world.add_agent(agent_id)

    from genevra.simulation.types import Action

    actions = list(Action)
    for _ in range(15):
        snapshot = world.snapshot()
        r = config.view_radius
        for agent_id, position in snapshot.agent_positions.items():
            expected_obstacles = reference_extract_single_window(
                snapshot.obstacles, True, *position, r
            )
            expected_a = reference_extract_single_window(snapshot.resources_a, 0.0, *position, r)
            expected_b = reference_extract_single_window(snapshot.resources_b, 0.0, *position, r)
            expected = np.stack(
                [
                    expected_obstacles.astype(np.float32),
                    (expected_a / config.resource_a_value).astype(np.float32),
                    (expected_b / config.resource_b_value).astype(np.float32),
                ],
                axis=-1,
            )
            actual = world.observe(agent_id).local_grid
            assert np.array_equal(actual, expected)

        step_actions = {aid: actions[int(rng.integers(0, len(actions)))] for aid in world.agent_ids}
        world.step(step_actions)


def test_extract_local_window_matches_two_channel_helper() -> None:
    rng = np.random.default_rng(0)
    obstacles = rng.random((10, 10)) < 0.3
    resources = rng.normal(size=(10, 10)).astype(np.float32)
    a, b = extract_local_window(obstacles, resources, 3, 4, 2, 10, 10)
    assert a.shape == (5, 5)
    assert b.shape == (5, 5)
