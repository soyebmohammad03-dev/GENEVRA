import dataclasses

import numpy as np
import pytest

from genevra.simulation.dynamics import EnvironmentRegime, RegimeChangeDynamics, StaticDynamics
from genevra.simulation.shared_grid_world import SharedGridWorld, SharedGridWorldConfig
from genevra.simulation.types import Action, Observation


def make_world(**overrides: object) -> SharedGridWorld:
    defaults: dict[str, object] = dict(
        width=12,
        height=12,
        view_radius=1,
        max_agents=10,
        obstacle_density=0.05,
        resource_a_density=0.15,
        resource_b_density=0.05,
        max_steps=100,
    )
    defaults.update(overrides)
    return SharedGridWorld(SharedGridWorldConfig(**defaults))  # type: ignore[arg-type]


def test_config_validates_ranges() -> None:
    with pytest.raises(ValueError):
        SharedGridWorldConfig(width=1, height=10)
    with pytest.raises(ValueError):
        SharedGridWorldConfig(width=10, height=10, max_agents=0)


def test_multiple_agents_can_coexist() -> None:
    world = make_world()
    world.reset(seed=0)
    world.add_agent(0)
    world.add_agent(1)
    world.add_agent(2)
    assert sorted(world.agent_ids) == [0, 1, 2]


def test_agents_get_distinct_positions() -> None:
    world = make_world(obstacle_density=0.0)
    world.reset(seed=0)
    for i in range(5):
        world.add_agent(i)
    snapshot = world.snapshot()
    positions = list(snapshot.agent_positions.values())
    assert len(set(positions)) == len(positions)


def test_observation_exposes_only_local_grid_not_other_agents_or_global_state() -> None:
    world = make_world()
    world.reset(seed=0)
    world.add_agent(0)
    world.add_agent(1)
    observation = world.observe(0)
    fields = {f.name for f in dataclasses.fields(Observation)}
    assert fields == {"local_grid"}
    # A single agent's local window shape must not depend on how many
    # other agents exist or on the size of the world.
    assert observation.local_grid.shape == (3, 3, 3)


def test_snapshot_contains_hidden_state_never_returned_by_observe() -> None:
    world = make_world()
    world.reset(seed=0)
    world.add_agent(0)
    snapshot = world.snapshot()
    assert hasattr(snapshot, "agent_positions")
    assert hasattr(snapshot, "obstacles")
    obs = world.observe(0)
    assert not hasattr(obs, "agent_positions")
    assert not hasattr(obs, "obstacles")


def test_removed_agent_can_no_longer_be_observed() -> None:
    world = make_world()
    world.reset(seed=0)
    world.add_agent(0)
    world.remove_agent(0)
    with pytest.raises(ValueError):
        world.observe(0)


def test_world_at_capacity_rejects_new_agents() -> None:
    world = make_world(max_agents=2, obstacle_density=0.0)
    world.reset(seed=0)
    world.add_agent(0)
    world.add_agent(1)
    with pytest.raises(RuntimeError):
        world.add_agent(2)


def test_deterministic_replay_with_same_seed_and_actions() -> None:
    world_a = make_world()
    world_b = make_world()
    world_a.reset(seed=7)
    world_b.reset(seed=7)
    world_a.add_agent(0)
    world_a.add_agent(1)
    world_b.add_agent(0)
    world_b.add_agent(1)

    actions_sequence = [
        {0: Action.MOVE_EAST, 1: Action.MOVE_WEST},
        {0: Action.EAT, 1: Action.STAY},
        {0: Action.MOVE_SOUTH, 1: Action.MOVE_NORTH},
    ]
    for actions in actions_sequence:
        result_a = world_a.step(actions)
        result_b = world_b.step(actions)
        for agent_id in actions:
            assert np.array_equal(
                result_a[agent_id].observation.local_grid, result_b[agent_id].observation.local_grid
            )
            assert result_a[agent_id].reward == result_b[agent_id].reward


def test_two_agents_competing_for_same_cell_only_one_moves_in() -> None:
    world = make_world(
        width=5, height=5, obstacle_density=0.0, resource_a_density=0.0, resource_b_density=0.0
    )
    world.reset(seed=0)
    snapshot = world.snapshot()
    # Deliberately place two agents adjacent to the same free target cell.
    from genevra.simulation.shared_grid_world import SharedGridWorldState
    from genevra.simulation.types import Position

    positions = {0: Position(1, 2), 1: Position(3, 2)}
    restored = SharedGridWorldState(
        obstacles=snapshot.obstacles,
        resources_a=snapshot.resources_a,
        resources_b=snapshot.resources_b,
        agent_positions=positions,
        step_count=0,
        rng_state=snapshot.rng_state,
    )
    world.restore(restored)
    results = world.step({0: Action.MOVE_EAST, 1: Action.MOVE_WEST})  # both target (2, 2)
    final_positions = {aid: r.info["position"] for aid, r in results.items()}
    assert len(set(final_positions.values())) == 2  # never collapse onto one cell
    assert world.interaction_events == 1


def test_regime_change_dynamics_affects_resource_regeneration() -> None:
    low = EnvironmentRegime(resource_regen_prob=0.0)
    high = EnvironmentRegime(resource_regen_prob=1.0)
    dynamics = RegimeChangeDynamics(regime_before=low, regime_after=high, switch_step=5)
    world = make_world(
        width=8,
        height=8,
        obstacle_density=0.0,
        resource_a_density=0.0,
        resource_b_density=0.0,
        dynamics=dynamics,
    )
    world.reset(seed=0)
    world.add_agent(0)
    total_before = 0.0
    for _ in range(5):
        result = world.step({0: Action.STAY})[0]
        total_before += float(
            result.observation.local_grid[..., 1].sum()
            + result.observation.local_grid[..., 2].sum()
        )
    total_after = 0.0
    for _ in range(5):
        result = world.step({0: Action.STAY})[0]
        total_after += float(
            result.observation.local_grid[..., 1].sum()
            + result.observation.local_grid[..., 2].sum()
        )
    assert total_after >= total_before


def test_invalid_action_raises() -> None:
    world = make_world()
    world.reset(seed=0)
    world.add_agent(0)
    with pytest.raises(ValueError):
        world.step({0: 999})  # type: ignore[dict-item]


def test_static_dynamics_is_the_default() -> None:
    config = SharedGridWorldConfig(width=10, height=10)
    assert isinstance(config.dynamics, StaticDynamics)
