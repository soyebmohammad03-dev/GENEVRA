"""Scientific invariant: an organism's `Observation` must never leak
simulator-internal state (absolute position, step count, RNG state, the
full grid). This is checked structurally (the dataclass has exactly one
field) and behaviorally (identical local surroundings at different
absolute positions produce identical observations).
"""

import dataclasses

import numpy as np

from genevra.simulation.grid_world import GridWorld, GridWorldConfig
from genevra.simulation.types import Action, Observation


def test_observation_exposes_only_local_grid() -> None:
    fields = {f.name for f in dataclasses.fields(Observation)}
    assert fields == {"local_grid"}


def test_observation_shape_matches_view_radius_not_world_size() -> None:
    world = GridWorld(GridWorldConfig(width=40, height=40, view_radius=1))
    obs = world.reset(seed=0)
    # A 40x40 world must not leak into a bigger-than-view observation.
    assert obs.local_grid.shape == (3, 3, 2)


def test_identical_local_surroundings_yield_identical_observations_at_different_positions() -> None:
    world = GridWorld(
        GridWorldConfig(
            width=10,
            height=10,
            view_radius=1,
            obstacle_density=0.0,
            resource_density=0.0,
            resource_regen_prob=0.0,
        )
    )
    world.reset(seed=0)
    obs_a = world.observe()
    world.step(Action.MOVE_EAST)
    obs_b = world.observe()
    # An open, resource-free world looks identical from any interior cell —
    # if absolute position leaked into the observation, this would fail.
    assert np.array_equal(obs_a.local_grid, obs_b.local_grid)


def test_step_info_is_not_reachable_from_observation() -> None:
    world = GridWorld(GridWorldConfig(width=10, height=10, view_radius=1))
    world.reset(seed=0)
    result = world.step(Action.STAY)
    assert "position" in result.info
    assert not hasattr(result.observation, "position")
    assert not hasattr(result.observation, "step_count")
