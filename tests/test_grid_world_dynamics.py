from genevra.simulation.dynamics import EnvironmentRegime, RegimeChangeDynamics
from genevra.simulation.grid_world import GridWorld, GridWorldConfig
from genevra.simulation.types import Action


def test_default_dynamics_is_none_and_uses_fixed_regen_prob() -> None:
    config = GridWorldConfig(width=9, height=9)
    assert config.dynamics is None


def test_dynamics_overrides_regen_prob() -> None:
    dynamics = RegimeChangeDynamics(
        regime_before=EnvironmentRegime(resource_regen_prob=0.0),
        regime_after=EnvironmentRegime(resource_regen_prob=1.0),
        switch_step=5,
    )
    world = GridWorld(
        GridWorldConfig(
            width=8,
            height=8,
            obstacle_density=0.0,
            resource_density=0.0,
            resource_regen_prob=0.0,
            dynamics=dynamics,
        )
    )
    world.reset(seed=0)
    total_before = 0.0
    for _ in range(5):
        result = world.step(Action.STAY)
        total_before += float(result.observation.local_grid[..., 1].sum())
    total_after = 0.0
    for _ in range(5):
        result = world.step(Action.STAY)
        total_after += float(result.observation.local_grid[..., 1].sum())
    assert total_before == 0.0  # regime_before has regen_prob=0.0
    assert total_after > 0.0  # regime_after has regen_prob=1.0
