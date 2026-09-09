"""Integration tests: an organism actually living inside a GridWorld.

These protect the highest-value invariants: the organism can only ever act
on `Observation` (never simulator-hidden state), and the same
(genome, seeds) pair replays identically while different seeds can diverge.
"""

import numpy as np

from genevra.organism.genome import ControllerArchitecture, Genome
from genevra.organism.learning import NoLearning
from genevra.organism.organism import Organism, OrganismConfig
from genevra.simulation.grid_world import GridWorld, GridWorldConfig
from genevra.simulation.types import Action

_VIEW_RADIUS = 1
_MEMORY_SIZE = 4
_GRID_FEATURES = (2 * _VIEW_RADIUS + 1) ** 2 * 2
_INPUT_SIZE = _GRID_FEATURES + 2 + _MEMORY_SIZE


def _build(env_seed: int, genome_seed: int, organism_rng_seed: int) -> tuple[Organism, GridWorld]:
    arch = ControllerArchitecture(input_size=_INPUT_SIZE, hidden_size=6, output_size=6)
    genome = Genome.random(arch, np.random.default_rng(genome_seed))
    config = OrganismConfig(view_radius=_VIEW_RADIUS, memory_size=_MEMORY_SIZE, initial_energy=30.0)
    organism = Organism(genome, config, NoLearning(), np.random.default_rng(organism_rng_seed))
    world = GridWorld(
        GridWorldConfig(width=9, height=9, view_radius=_VIEW_RADIUS, obstacle_density=0.1)
    )
    world.reset(seed=env_seed)
    return organism, world


def _run_lifetime(organism: Organism, world: GridWorld, steps: int) -> list[Action]:
    observation = world.observe()
    actions_taken: list[Action] = []
    for _ in range(steps):
        if not organism.is_alive:
            break
        action = organism.act(observation)
        actions_taken.append(action)
        result = world.step(action)
        organism.learn_from_feedback(action, resource_gained=result.reward)
        observation = result.observation
    return actions_taken


def test_identical_seeds_produce_identical_trajectories() -> None:
    organism_a, world_a = _build(env_seed=5, genome_seed=1, organism_rng_seed=9)
    organism_b, world_b = _build(env_seed=5, genome_seed=1, organism_rng_seed=9)

    actions_a = _run_lifetime(organism_a, world_a, steps=30)
    actions_b = _run_lifetime(organism_b, world_b, steps=30)

    assert actions_a == actions_b
    assert organism_a.metabolism.energy == organism_b.metabolism.energy


def test_different_organism_rng_can_diverge_trajectories() -> None:
    organism_a, world_a = _build(env_seed=5, genome_seed=1, organism_rng_seed=9)
    organism_b, world_b = _build(env_seed=5, genome_seed=1, organism_rng_seed=10)

    actions_a = _run_lifetime(organism_a, world_a, steps=30)
    actions_b = _run_lifetime(organism_b, world_b, steps=30)

    assert actions_a != actions_b


def test_different_environment_seeds_can_diverge_trajectories() -> None:
    organism_a, world_a = _build(env_seed=1, genome_seed=1, organism_rng_seed=9)
    organism_b, world_b = _build(env_seed=2, genome_seed=1, organism_rng_seed=9)

    actions_a = _run_lifetime(organism_a, world_a, steps=40)
    actions_b = _run_lifetime(organism_b, world_b, steps=40)

    assert actions_a != actions_b


def test_organism_only_ever_receives_observation_objects() -> None:
    """Structural guarantee: `Organism.act` accepts an `Observation`, and
    the local grid it reads has the view-limited shape, not the full
    world grid — sourced from the environment's public interface only."""
    organism, world = _build(env_seed=0, genome_seed=0, organism_rng_seed=0)
    observation = world.observe()
    action = organism.act(observation)
    assert isinstance(action, Action)
    assert observation.local_grid.shape == (2 * _VIEW_RADIUS + 1, 2 * _VIEW_RADIUS + 1, 2)
    world_state = world.snapshot()
    assert observation.local_grid.shape != world_state.obstacles.shape


def test_energy_depletes_and_organism_eventually_dies_without_food() -> None:
    organism, world = _build(env_seed=3, genome_seed=2, organism_rng_seed=4)
    _run_lifetime(organism, world, steps=500)
    # With random movement costs and only rare resource regen, a 500-step
    # lifetime from initial_energy=30 should exhaust the energy budget.
    assert not organism.is_alive
