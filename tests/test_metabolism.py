from genevra.organism.metabolism import MetabolicParams, Metabolism
from genevra.simulation.types import Action


def make_metabolism(initial_energy: float = 10.0) -> Metabolism:
    params = MetabolicParams(move_cost=1.0, stay_cost=0.2, eat_cost=0.1, base_upkeep=0.05)
    return Metabolism(params, initial_energy)


def test_movement_costs_more_than_staying() -> None:
    metabolism = make_metabolism()
    assert metabolism.cost_for(Action.MOVE_NORTH) > metabolism.cost_for(Action.STAY)


def test_apply_step_deducts_cost_and_upkeep() -> None:
    metabolism = make_metabolism(initial_energy=10.0)
    metabolism.apply_step(Action.STAY, resource_gained=0.0)
    assert metabolism.energy == 10.0 - 0.2 - 0.05


def test_resource_gain_offsets_cost() -> None:
    metabolism = make_metabolism(initial_energy=10.0)
    metabolism.apply_step(Action.EAT, resource_gained=5.0)
    assert metabolism.energy == 10.0 - 0.1 - 0.05 + 5.0


def test_is_alive_reflects_energy_sign() -> None:
    metabolism = make_metabolism(initial_energy=0.1)
    assert metabolism.is_alive
    metabolism.apply_step(Action.MOVE_NORTH, resource_gained=0.0)
    assert not metabolism.is_alive


def test_repeated_movement_without_food_leads_to_death() -> None:
    metabolism = make_metabolism(initial_energy=3.0)
    for _ in range(10):
        if not metabolism.is_alive:
            break
        metabolism.apply_step(Action.MOVE_NORTH, resource_gained=0.0)
    assert not metabolism.is_alive
