import numpy as np

from genevra.evolution.lifetime import LifetimeObservations, run_single_lifetime
from genevra.metrics.adaptation import compute_adaptation_curve
from genevra.organism.genome import ControllerArchitecture, Genome
from genevra.organism.learning import HebbianLearning, NoLearning
from genevra.organism.organism import OrganismConfig
from genevra.simulation.grid_world import GridWorldConfig


def make_observations(rewards: list[float]) -> LifetimeObservations:
    return LifetimeObservations(
        steps_survived=len(rewards),
        total_resource_gained=sum(rewards),
        final_energy=0.0,
        positions_visited=(),
        actions_taken=(),
        survived_full_lifetime=True,
        rewards_by_step=tuple(rewards),
    )


def test_learning_gain_is_zero_for_flat_reward_signal() -> None:
    curve = compute_adaptation_curve(make_observations([1.0] * 20), window=5)
    assert curve.learning_gain == 0.0
    assert curve.initial_competence == curve.final_competence == 1.0


def test_learning_gain_positive_for_rising_reward_signal() -> None:
    rewards = [0.0] * 10 + [5.0] * 10
    curve = compute_adaptation_curve(make_observations(rewards), window=5)
    assert curve.learning_gain > 0.0
    assert curve.initial_competence == 0.0
    assert curve.final_competence == 5.0


def test_learning_gain_negative_for_declining_reward_signal() -> None:
    rewards = [5.0] * 10 + [0.0] * 10
    curve = compute_adaptation_curve(make_observations(rewards), window=5)
    assert curve.learning_gain < 0.0


def test_short_lifetime_uses_overlapping_reduced_window() -> None:
    curve = compute_adaptation_curve(make_observations([1.0, 2.0, 3.0]), window=10)
    assert curve.window_size == 3
    assert curve.steps_survived == 3


def test_empty_lifetime_reports_zero_without_crashing() -> None:
    curve = compute_adaptation_curve(make_observations([]), window=5)
    assert curve.steps_survived == 0
    assert curve.learning_gain == 0.0


def test_rewards_by_step_matches_total_resource_gained_end_to_end() -> None:
    """`run_single_lifetime` must actually populate rewards_by_step
    consistently with total_resource_gained — not a value invented after
    the fact."""
    architecture = ControllerArchitecture(input_size=22, hidden_size=6, output_size=6)
    rng = np.random.default_rng(0)
    genome = Genome.random(architecture, rng)
    organism_config = OrganismConfig(view_radius=1, memory_size=2, initial_energy=20.0)
    env_config = GridWorldConfig(width=10, height=10, view_radius=1, max_steps=30)

    observations = run_single_lifetime(
        genome=genome,
        environment_config=env_config,
        organism_config=organism_config,
        learning_rule=NoLearning(),
        env_seed=1,
        organism_seed=2,
        max_steps=30,
    )
    assert len(observations.rewards_by_step) == observations.steps_survived
    assert np.isclose(sum(observations.rewards_by_step), observations.total_resource_gained)


def test_hebbian_vs_no_learning_produce_different_adaptation_curves_on_same_seed() -> None:
    """Not a claim that Hebbian learning always improves learning_gain —
    only that the mechanism actually changes the observed curve versus
    the NoLearning control under otherwise identical conditions."""
    architecture = ControllerArchitecture(input_size=22, hidden_size=6, output_size=6)
    rng = np.random.default_rng(0)
    genome = Genome.random(architecture, rng)
    genome.learning_genes[:] = [0.3, 1.0, 0.0]
    organism_config = OrganismConfig(view_radius=1, memory_size=2, initial_energy=20.0)
    env_config = GridWorldConfig(width=10, height=10, view_radius=1, max_steps=40)

    obs_no_learning = run_single_lifetime(
        genome=genome,
        environment_config=env_config,
        organism_config=organism_config,
        learning_rule=NoLearning(),
        env_seed=5,
        organism_seed=5,
        max_steps=40,
    )
    obs_hebbian = run_single_lifetime(
        genome=genome,
        environment_config=env_config,
        organism_config=organism_config,
        learning_rule=HebbianLearning(),
        env_seed=5,
        organism_seed=5,
        max_steps=40,
    )
    curve_no_learning = compute_adaptation_curve(obs_no_learning)
    curve_hebbian = compute_adaptation_curve(obs_hebbian)
    assert obs_no_learning.rewards_by_step != obs_hebbian.rewards_by_step or (
        curve_no_learning.learning_gain != curve_hebbian.learning_gain
    )
