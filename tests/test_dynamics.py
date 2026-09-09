import numpy as np

from genevra.simulation.dynamics import (
    EnvironmentRegime,
    PeriodicDynamics,
    RegimeChangeDynamics,
    StaticDynamics,
    StochasticDynamics,
)


def test_static_dynamics_never_changes() -> None:
    regime = EnvironmentRegime(resource_regen_prob=0.05)
    dynamics = StaticDynamics(regime)
    rng = np.random.default_rng(0)
    assert dynamics.regime_at(0, rng) == regime
    assert dynamics.regime_at(1000, rng) == regime


def test_periodic_dynamics_alternates_deterministically() -> None:
    a = EnvironmentRegime(resource_regen_prob=0.01)
    b = EnvironmentRegime(resource_regen_prob=0.5)
    dynamics = PeriodicDynamics(regime_a=a, regime_b=b, period=10)
    rng = np.random.default_rng(0)
    assert dynamics.regime_at(0, rng) == a
    assert dynamics.regime_at(4, rng) == a
    assert dynamics.regime_at(5, rng) == b
    assert dynamics.regime_at(9, rng) == b
    assert dynamics.regime_at(10, rng) == a  # next cycle


def test_regime_change_switches_once_at_configured_step() -> None:
    before = EnvironmentRegime(resource_regen_prob=0.01)
    after = EnvironmentRegime(resource_regen_prob=0.5)
    dynamics = RegimeChangeDynamics(regime_before=before, regime_after=after, switch_step=20)
    rng = np.random.default_rng(0)
    assert dynamics.regime_at(0, rng) == before
    assert dynamics.regime_at(19, rng) == before
    assert dynamics.regime_at(20, rng) == after
    assert dynamics.regime_at(1000, rng) == after


def test_stochastic_dynamics_is_reproducible_given_same_rng_sequence() -> None:
    base = EnvironmentRegime(resource_regen_prob=0.1)
    dynamics = StochasticDynamics(base_regime=base, regen_prob_std=0.05)
    a = [dynamics.regime_at(i, np.random.default_rng(0)) for i in range(5)]
    b = [dynamics.regime_at(i, np.random.default_rng(0)) for i in range(5)]
    assert a == b


def test_stochastic_dynamics_stays_within_bounds() -> None:
    base = EnvironmentRegime(resource_regen_prob=0.05)
    dynamics = StochasticDynamics(base_regime=base, regen_prob_std=1.0)
    rng = np.random.default_rng(1)
    for step in range(50):
        regime = dynamics.regime_at(step, rng)
        assert 0.0 <= regime.resource_regen_prob <= 1.0


def test_regime_rejects_out_of_range_probability() -> None:
    import pytest

    with pytest.raises(ValueError):
        EnvironmentRegime(resource_regen_prob=1.5)
