import numpy as np

from genevra.evolution.lifetime import LifetimeObservations
from genevra.metrics.behavior import SIGNATURE_LENGTH, behavioral_signature
from genevra.simulation.types import Action, Position


def test_signature_has_fixed_length() -> None:
    observations = LifetimeObservations(
        steps_survived=5,
        total_resource_gained=3.0,
        final_energy=1.0,
        positions_visited=(
            Position(0, 0),
            Position(1, 0),
            Position(2, 0),
            Position(2, 1),
            Position(2, 2),
        ),
        actions_taken=(
            Action.MOVE_EAST,
            Action.MOVE_EAST,
            Action.MOVE_SOUTH,
            Action.MOVE_SOUTH,
            Action.STAY,
        ),
        survived_full_lifetime=False,
    )
    signature = behavioral_signature(observations)
    assert signature.shape == (SIGNATURE_LENGTH,)


def test_empty_lifetime_produces_zero_signature() -> None:
    observations = LifetimeObservations(
        steps_survived=0,
        total_resource_gained=0.0,
        final_energy=0.0,
        positions_visited=(),
        actions_taken=(),
        survived_full_lifetime=False,
    )
    signature = behavioral_signature(observations)
    assert signature.shape == (SIGNATURE_LENGTH,)
    assert np.all(signature == 0.0)


def test_different_action_distributions_give_different_signatures() -> None:
    base_positions = (Position(0, 0),) * 5
    stay_only = LifetimeObservations(
        steps_survived=5,
        total_resource_gained=0.0,
        final_energy=0.0,
        positions_visited=base_positions,
        actions_taken=(Action.STAY,) * 5,
        survived_full_lifetime=False,
    )
    eat_only = LifetimeObservations(
        steps_survived=5,
        total_resource_gained=0.0,
        final_energy=0.0,
        positions_visited=base_positions,
        actions_taken=(Action.EAT,) * 5,
        survived_full_lifetime=False,
    )
    assert not np.array_equal(behavioral_signature(stay_only), behavioral_signature(eat_only))


def test_signature_is_deterministic() -> None:
    observations = LifetimeObservations(
        steps_survived=3,
        total_resource_gained=2.0,
        final_energy=1.0,
        positions_visited=(Position(0, 0), Position(1, 1), Position(2, 2)),
        actions_taken=(Action.MOVE_EAST, Action.MOVE_SOUTH, Action.STAY),
        survived_full_lifetime=True,
    )
    a = behavioral_signature(observations)
    b = behavioral_signature(observations)
    assert np.array_equal(a, b)
