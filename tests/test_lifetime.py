import numpy as np

from genevra.evolution.lifetime import run_single_lifetime
from genevra.organism.genome import ControllerArchitecture, Genome
from genevra.organism.learning import NoLearning
from genevra.organism.organism import OrganismConfig
from genevra.simulation.grid_world import GridWorldConfig

_VIEW_RADIUS = 1
_MEMORY_SIZE = 4
_INPUT_SIZE = (2 * _VIEW_RADIUS + 1) ** 2 * 2 + 2 + _MEMORY_SIZE


def _config() -> tuple[Genome, GridWorldConfig, OrganismConfig]:
    arch = ControllerArchitecture(input_size=_INPUT_SIZE, hidden_size=6, output_size=6)
    genome = Genome.random(arch, np.random.default_rng(0))
    env_config = GridWorldConfig(width=9, height=9, view_radius=_VIEW_RADIUS, max_steps=40)
    organism_config = OrganismConfig(
        view_radius=_VIEW_RADIUS, memory_size=_MEMORY_SIZE, initial_energy=20.0
    )
    return genome, env_config, organism_config


def test_lifetime_produces_bounded_observations() -> None:
    genome, env_config, organism_config = _config()
    observations = run_single_lifetime(
        genome, env_config, organism_config, NoLearning(), env_seed=1, organism_seed=2, max_steps=40
    )
    assert 0 <= observations.steps_survived <= 40
    assert len(observations.actions_taken) == observations.steps_survived
    assert len(observations.positions_visited) == observations.steps_survived


def test_lifetime_is_deterministic_given_same_seeds() -> None:
    genome, env_config, organism_config = _config()
    a = run_single_lifetime(
        genome, env_config, organism_config, NoLearning(), env_seed=5, organism_seed=6, max_steps=40
    )
    b = run_single_lifetime(
        genome, env_config, organism_config, NoLearning(), env_seed=5, organism_seed=6, max_steps=40
    )
    assert a == b or (
        a.steps_survived == b.steps_survived
        and a.total_resource_gained == b.total_resource_gained
        and a.final_energy == b.final_energy
        and a.actions_taken == b.actions_taken
        and a.positions_visited == b.positions_visited
    )


def test_survived_full_lifetime_flag_matches_step_count() -> None:
    genome, env_config, organism_config = _config()
    observations = run_single_lifetime(
        genome, env_config, organism_config, NoLearning(), env_seed=1, organism_seed=2, max_steps=40
    )
    assert observations.survived_full_lifetime == (observations.steps_survived == 40)
