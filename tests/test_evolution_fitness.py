from genevra.evolution.fitness import SurvivalResourceFitness
from genevra.evolution.lifetime import LifetimeObservations
from genevra.simulation.types import Action, Position


def make_observations(steps: int, resources: float) -> LifetimeObservations:
    return LifetimeObservations(
        steps_survived=steps,
        total_resource_gained=resources,
        final_energy=1.0,
        positions_visited=(Position(0, 0),) * steps,
        actions_taken=(Action.STAY,) * steps,
        survived_full_lifetime=False,
    )


def test_fitness_combines_survival_and_resources() -> None:
    fitness_fn = SurvivalResourceFitness(survival_weight=1.0, resource_weight=2.0)
    observations = make_observations(steps=10, resources=5.0)
    assert fitness_fn.compute(observations) == 10 * 1.0 + 5.0 * 2.0


def test_zero_weight_ignores_that_component() -> None:
    fitness_fn = SurvivalResourceFitness(survival_weight=0.0, resource_weight=1.0)
    observations = make_observations(steps=100, resources=3.0)
    assert fitness_fn.compute(observations) == 3.0
