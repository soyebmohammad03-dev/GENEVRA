import numpy as np
import pytest

from genevra.organism.genome import ControllerArchitecture, Genome
from genevra.organism.learning import HebbianLearning, NoLearning
from genevra.organism.mutation import GaussianMutation
from genevra.organism.organism import Organism, OrganismConfig
from genevra.organism.reproduction import ReproductionSystem
from genevra.simulation.grid_world import GridWorld, GridWorldConfig


def make_organism(learning_rule=None) -> tuple[Organism, GridWorld]:
    view_radius = 1
    memory_size = 4
    grid_features = (2 * view_radius + 1) ** 2 * 2
    input_size = grid_features + 2 + memory_size  # + energy, last action

    arch = ControllerArchitecture(input_size=input_size, hidden_size=6, output_size=6)
    genome = Genome.random(arch, np.random.default_rng(0))
    config = OrganismConfig(view_radius=view_radius, memory_size=memory_size, initial_energy=20.0)
    organism = Organism(genome, config, learning_rule or NoLearning(), np.random.default_rng(0))

    world = GridWorld(GridWorldConfig(width=9, height=9, view_radius=view_radius))
    world.reset(seed=0)
    return organism, world


def test_construction_rejects_mismatched_input_size() -> None:
    arch = ControllerArchitecture(input_size=3, hidden_size=4, output_size=6)
    genome = Genome.random(arch, np.random.default_rng(0))
    config = OrganismConfig(view_radius=1, memory_size=4, initial_energy=10.0)
    with pytest.raises(ValueError):
        Organism(genome, config, NoLearning(), np.random.default_rng(0))


def test_act_returns_a_valid_action() -> None:
    organism, world = make_organism()
    obs = world.observe()
    action = organism.act(obs)
    from genevra.simulation.types import Action

    assert isinstance(action, Action)


def test_act_is_deterministic_given_same_rng_state() -> None:
    organism_a, world_a = make_organism()
    organism_b, world_b = make_organism()
    # Reset organism RNGs to the same seed for a fair comparison.
    organism_a._rng = np.random.default_rng(7)
    organism_b._rng = np.random.default_rng(7)

    obs_a = world_a.observe()
    obs_b = world_b.observe()
    assert organism_a.act(obs_a) == organism_b.act(obs_b)


def test_learn_from_feedback_before_act_raises() -> None:
    organism, _world = make_organism()
    from genevra.simulation.types import Action

    with pytest.raises(RuntimeError):
        organism.learn_from_feedback(Action.STAY, resource_gained=0.0)


def test_metabolism_updates_after_feedback() -> None:
    organism, world = make_organism()
    obs = world.observe()
    action = organism.act(obs)
    energy_before = organism.metabolism.energy
    organism.learn_from_feedback(action, resource_gained=0.0)
    assert organism.metabolism.energy < energy_before


def test_hebbian_learning_state_changes_across_steps() -> None:
    organism, world = make_organism(learning_rule=HebbianLearning())
    initial_delta = organism._learning_state.output_weight_delta.copy()
    obs = world.observe()
    action = organism.act(obs)
    organism.learn_from_feedback(action, resource_gained=0.0)
    assert not np.array_equal(organism._learning_state.output_weight_delta, initial_delta)


def test_memory_updates_across_steps() -> None:
    organism, world = make_organism()
    initial_memory = organism.memory.state.copy()
    obs = world.observe()
    organism.act(obs)
    assert not np.array_equal(organism.memory.state, initial_memory)


def test_reproduction_requires_energy_threshold() -> None:
    organism, _world = make_organism()
    reproduction = ReproductionSystem(
        GaussianMutation(), energy_threshold=1000.0, offspring_energy_cost=5.0
    )
    assert not reproduction.can_reproduce(organism.metabolism)
    with pytest.raises(RuntimeError):
        reproduction.reproduce(organism.genome, organism.metabolism, np.random.default_rng(0))


def test_reproduction_produces_mutated_offspring_genome_and_costs_energy() -> None:
    organism, _world = make_organism()
    reproduction = ReproductionSystem(
        GaussianMutation(), energy_threshold=1.0, offspring_energy_cost=5.0
    )
    energy_before = organism.metabolism.energy
    offspring_genome = reproduction.reproduce(
        organism.genome, organism.metabolism, np.random.default_rng(0)
    )
    assert organism.metabolism.energy == energy_before - 5.0
    assert offspring_genome.architecture == organism.genome.architecture


def test_is_alive_reflects_metabolism() -> None:
    organism, world = make_organism()
    assert organism.is_alive
    obs = world.observe()
    for _ in range(200):
        action = organism.act(obs)
        organism.learn_from_feedback(action, resource_gained=0.0)
        if not organism.is_alive:
            break
    assert not organism.is_alive
