from genevra.evolution.continuous import ContinuousEvolutionConfig, ContinuousEvolutionEngine
from genevra.organism.genome import ControllerArchitecture
from genevra.organism.organism import OrganismConfig
from genevra.simulation.shared_grid_world import SharedGridWorldConfig
from genevra.simulation.types import Action

_VIEW_RADIUS = 1
_MEMORY_SIZE = 2
_INPUT_SIZE = (2 * _VIEW_RADIUS + 1) ** 2 * 3 + 2 + _MEMORY_SIZE  # 3 channels: shared world


def make_config(
    seed: int = 0, total_steps: int = 40, initial_population: int = 4
) -> ContinuousEvolutionConfig:
    architecture = ControllerArchitecture(
        input_size=_INPUT_SIZE, hidden_size=6, output_size=len(Action)
    )
    organism_config = OrganismConfig(
        view_radius=_VIEW_RADIUS, memory_size=_MEMORY_SIZE, initial_energy=15.0, channels=3
    )
    environment_config = SharedGridWorldConfig(
        width=10, height=10, view_radius=_VIEW_RADIUS, max_agents=12, max_steps=10_000
    )
    return ContinuousEvolutionConfig(
        total_steps=total_steps,
        initial_population=initial_population,
        max_population=8,
        environment_config=environment_config,
        architecture=architecture,
        organism_config=organism_config,
        reproduction_energy_threshold=-1000.0,  # always eligible, for deterministic birth testing
        offspring_energy_cost=1.0,
        seed=seed,
        log_every=5,
    )


def test_initialize_creates_founder_population() -> None:
    engine = ContinuousEvolutionEngine(make_config())
    engine.initialize()
    assert len(engine.population) == 4
    for living in engine.population.values():
        assert living.birth_step == 0
        assert living.parent_ids == ()


def test_population_ages_over_time() -> None:
    engine = ContinuousEvolutionEngine(make_config(total_steps=20))
    engine.initialize()
    for _ in range(10):
        engine._tick()
    ages = [
        living.age_at(engine.step_index)
        for living in engine.population.values()
        if living.birth_step == 0
    ]
    assert all(age == 10 for age in ages)


def test_population_never_exceeds_max_population() -> None:
    engine = ContinuousEvolutionEngine(make_config(total_steps=60))
    engine.run()
    assert len(engine.population) <= 8


def test_births_and_deaths_are_recorded_in_lineage() -> None:
    engine = ContinuousEvolutionEngine(make_config(total_steps=60))
    engine.run()
    events = engine.lineage.to_dicts()
    assert len(events) >= 4  # at least the founders
    births_after_founders = [e for e in events if e["generation"] > 0]
    # With an always-eligible reproduction threshold and spare capacity,
    # at least one birth should have happened during 60 steps.
    assert len(births_after_founders) > 0


def test_history_is_recorded_at_configured_frequency_not_every_step() -> None:
    engine = ContinuousEvolutionEngine(make_config(total_steps=23))
    engine.run()
    # log_every=5 over 23 steps (0..22): snapshots at 0, 5, 10, 15, 20 -> 5 entries.
    assert len(engine.history) == 5
    assert [s.step for s in engine.history] == [0, 5, 10, 15, 20]


def test_run_is_deterministic_given_same_seed() -> None:
    engine_a = ContinuousEvolutionEngine(make_config(seed=3, total_steps=30))
    engine_b = ContinuousEvolutionEngine(make_config(seed=3, total_steps=30))
    history_a = engine_a.run()
    history_b = engine_b.run()
    assert [s.population_size for s in history_a] == [s.population_size for s in history_b]
    assert [s.mean_energy for s in history_a] == [s.mean_energy for s in history_b]
    assert [s.births_since_last_snapshot for s in history_a] == [
        s.births_since_last_snapshot for s in history_b
    ]


def test_different_seeds_can_diverge() -> None:
    engine_a = ContinuousEvolutionEngine(make_config(seed=1, total_steps=30))
    engine_b = ContinuousEvolutionEngine(make_config(seed=2, total_steps=30))
    history_a = engine_a.run()
    history_b = engine_b.run()
    assert [s.mean_energy for s in history_a] != [s.mean_energy for s in history_b]


def test_organisms_can_die_and_population_can_shrink() -> None:
    config = make_config(total_steps=200, initial_population=4)
    # Force starvation: make reproduction essentially impossible so the
    # population can only shrink, never be replenished.
    starving_config = ContinuousEvolutionConfig(
        total_steps=config.total_steps,
        initial_population=config.initial_population,
        max_population=config.max_population,
        environment_config=config.environment_config,
        architecture=config.architecture,
        organism_config=config.organism_config,
        reproduction_energy_threshold=1_000_000.0,
        offspring_energy_cost=config.offspring_energy_cost,
        seed=0,
        log_every=10,
    )
    engine = ContinuousEvolutionEngine(starving_config)
    engine.run()
    assert len(engine.population) < 4
