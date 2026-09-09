import numpy as np

from genevra.simulation.environment import Environment, VectorEnvironment
from genevra.simulation.grid_world import GridWorld, GridWorldConfig
from genevra.simulation.types import Action


def make_world(width: int = 7, height: int = 7) -> GridWorld:
    return GridWorld(GridWorldConfig(width=width, height=height, view_radius=1))


def test_grid_world_satisfies_environment_protocol() -> None:
    world = make_world()
    assert isinstance(world, Environment)


def test_vector_environment_resets_each_instance_independently() -> None:
    envs = VectorEnvironment([make_world(), make_world(), make_world()])
    observations = envs.reset([1, 2, 3])
    assert len(observations) == 3
    assert len(envs) == 3
    # Different seeds over a stochastic world should not all be identical.
    assert not (
        np.array_equal(observations[0].local_grid, observations[1].local_grid)
        and np.array_equal(observations[1].local_grid, observations[2].local_grid)
    )


def test_vector_environment_steps_all_instances_with_matched_actions() -> None:
    envs = VectorEnvironment([make_world(), make_world()])
    envs.reset([0, 0])
    results = envs.step([Action.MOVE_EAST, Action.STAY])
    assert len(results) == 2
    # MOVE_EAST vs STAY on identically-seeded worlds must diverge position.
    assert results[0].info["position"] != results[1].info["position"]
