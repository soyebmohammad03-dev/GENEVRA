from genevra.evolution.engine import EvolutionConfig, EvolutionEngine, RunStatus
from genevra.evolution.fitness import SurvivalResourceFitness
from genevra.evolution.population import PopulationConfig
from genevra.evolution.reproduction import PopulationReproductionConfig
from genevra.evolution.selection import TournamentSelection
from genevra.organism.genome import ControllerArchitecture
from genevra.organism.learning import NoLearning
from genevra.organism.mutation import GaussianMutation
from genevra.organism.organism import OrganismConfig
from genevra.simulation.grid_world import GridWorldConfig
from genevra.simulation.types import Action

_VIEW_RADIUS = 1
_MEMORY_SIZE = 2
_INPUT_SIZE = (2 * _VIEW_RADIUS + 1) ** 2 * 2 + 2 + _MEMORY_SIZE


def make_evolution_config(
    seed: int, generations: int = 3, population_size: int = 6, energy_threshold: float = 3.0
) -> EvolutionConfig:
    architecture = ControllerArchitecture(
        input_size=_INPUT_SIZE, hidden_size=5, output_size=len(Action)
    )
    organism_config = OrganismConfig(
        view_radius=_VIEW_RADIUS, memory_size=_MEMORY_SIZE, initial_energy=15.0
    )
    population_config = PopulationConfig(
        size=population_size, architecture=architecture, organism_config=organism_config
    )
    environment_config = GridWorldConfig(width=9, height=9, view_radius=_VIEW_RADIUS, max_steps=25)
    return EvolutionConfig(
        generations=generations,
        steps_per_lifetime=25,
        environment_config=environment_config,
        population_config=population_config,
        fitness_function=SurvivalResourceFitness(),
        selection_strategy=TournamentSelection(tournament_size=3),
        reproduction=PopulationReproductionConfig(
            energy_threshold=energy_threshold, mutation_operator=GaussianMutation()
        ),
        learning_rule_factory=NoLearning,
        seed=seed,
    )


def test_initialize_creates_founder_population_and_lineage() -> None:
    engine = EvolutionEngine(make_evolution_config(seed=0))
    engine.initialize()
    assert engine.population.size == 6
    assert len(engine.lineage) == 6
    assert engine.status == RunStatus.RUNNING


def test_step_advances_generation_and_preserves_population_size() -> None:
    engine = EvolutionEngine(make_evolution_config(seed=0, energy_threshold=-1000.0))
    engine.initialize()
    engine.step()
    assert engine.generation == 1
    assert engine.population.size == 6  # non-overlapping generations: full replacement


def test_offspring_parent_ids_reference_the_previous_generation() -> None:
    engine = EvolutionEngine(make_evolution_config(seed=0, energy_threshold=-1000.0))
    engine.initialize()
    parent_ids = {individual.id for individual in engine.population.individuals}
    engine.step()
    for individual in engine.population.individuals:
        assert individual.generation == 1
        assert set(individual.parent_ids).issubset(parent_ids)


def test_run_produces_one_snapshot_per_generation() -> None:
    engine = EvolutionEngine(make_evolution_config(seed=0, generations=4, energy_threshold=-1000.0))
    trajectory = engine.run()
    assert len(trajectory) == 4
    assert [s.generation for s in trajectory.snapshots] == [0, 1, 2, 3]


def test_run_is_fully_deterministic_given_same_seed() -> None:
    engine_a = EvolutionEngine(
        make_evolution_config(seed=42, generations=3, energy_threshold=-1000.0)
    )
    engine_b = EvolutionEngine(
        make_evolution_config(seed=42, generations=3, energy_threshold=-1000.0)
    )
    trajectory_a = engine_a.run()
    trajectory_b = engine_b.run()

    for snap_a, snap_b in zip(trajectory_a.snapshots, trajectory_b.snapshots, strict=True):
        assert snap_a.fitness_summary == snap_b.fitness_summary
        assert snap_a.genotypic_diversity == snap_b.genotypic_diversity
        assert snap_a.behavioral_diversity == snap_b.behavioral_diversity
        assert snap_a.mean_novelty == snap_b.mean_novelty

    final_genomes_a = [
        ind.genome.controller_weights.tolist() for ind in engine_a.population.individuals
    ]
    final_genomes_b = [
        ind.genome.controller_weights.tolist() for ind in engine_b.population.individuals
    ]
    assert final_genomes_a == final_genomes_b


def test_different_seeds_can_produce_different_trajectories() -> None:
    engine_a = EvolutionEngine(
        make_evolution_config(seed=1, generations=3, energy_threshold=-1000.0)
    )
    engine_b = EvolutionEngine(
        make_evolution_config(seed=2, generations=3, energy_threshold=-1000.0)
    )
    trajectory_a = engine_a.run()
    trajectory_b = engine_b.run()
    fitness_means_a = [s.fitness_summary.mean for s in trajectory_a.snapshots]
    fitness_means_b = [s.fitness_summary.mean for s in trajectory_b.snapshots]
    assert fitness_means_a != fitness_means_b


def test_extinction_when_no_individual_meets_reproduction_threshold() -> None:
    engine = EvolutionEngine(
        make_evolution_config(seed=0, generations=5, energy_threshold=1_000_000.0)
    )
    trajectory = engine.run()
    assert engine.status == RunStatus.EXTINCT
    assert engine.population.size == 0
    assert trajectory.snapshots[-1].extinction is True
    # The run must stop early rather than silently continuing with an
    # empty population.
    assert len(trajectory) < 5


def test_lineage_deaths_are_recorded_for_every_generation() -> None:
    engine = EvolutionEngine(make_evolution_config(seed=0, generations=2, energy_threshold=-1000.0))
    engine.run()
    events = engine.lineage.to_dicts()
    founder_events = [e for e in events if e["generation"] == 0]
    for event in founder_events:
        assert event["death_generation"] is not None
