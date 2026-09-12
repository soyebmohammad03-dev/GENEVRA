import numpy as np

from genevra.ecology.coevolution import CoEvolutionAnalyzer, run_coevolution_experiment
from genevra.ecology.competition import (
    compute_competition_metrics,
    gini_coefficient,
    herfindahl_index,
    pielou_evenness,
)
from genevra.ecology.hypotheses import (
    ALL_ECOLOGY_HYPOTHESES,
    H1_COMPETITION_CHANGES_LEARNING_STRATEGY,
    AssociationLabel,
)
from genevra.ecology.hypotheses import test_ecology_hypothesis as run_ecology_hypothesis_test
from genevra.ecology.interactions import (
    EcologicalContext,
    EcologicalInteraction,
    InteractionOutcome,
    InteractionType,
    build_interaction_network,
    derive_competition_interactions,
    derive_resource_acquisition_interactions,
    require_shared_grid_world_with_spatial_competition,
)
from genevra.ecology.network import EcologicalNetworkAnalyzer, interaction_turnover
from genevra.ecology.niches import (
    compute_niche_profile,
    resource_types_from_step_infos,
    summarize_population_niches,
)
from genevra.ecology.regime_transitions import detect_ecological_regime_transitions
from genevra.ecology.roles import EcologicalRole, classify_roles
from genevra.ecology.spatial import (
    Metapopulation,
    MigrationConfig,
    SpatialRegime,
    build_connectivity,
)
from genevra.evolution.continuous import ContinuousEvolutionConfig
from genevra.organism.genome import ControllerArchitecture
from genevra.organism.organism import OrganismConfig
from genevra.simulation.interaction import SpatialCompetition
from genevra.simulation.shared_grid_world import SharedGridWorld, SharedGridWorldConfig
from genevra.simulation.types import Action

_VIEW_RADIUS = 1
_MEMORY_SIZE = 2
_INPUT_SIZE = (2 * _VIEW_RADIUS + 1) ** 2 * 3 + 2 + _MEMORY_SIZE


def _make_patch_config(seed: int = 0, total_steps: int = 40) -> ContinuousEvolutionConfig:
    architecture = ControllerArchitecture(
        input_size=_INPUT_SIZE, hidden_size=6, output_size=len(Action)
    )
    organism_config = OrganismConfig(
        view_radius=_VIEW_RADIUS, memory_size=_MEMORY_SIZE, initial_energy=15.0, channels=3
    )
    environment_config = SharedGridWorldConfig(
        width=8, height=8, view_radius=_VIEW_RADIUS, max_agents=10, max_steps=10_000
    )
    return ContinuousEvolutionConfig(
        total_steps=total_steps,
        initial_population=6,
        max_population=10,
        environment_config=environment_config,
        architecture=architecture,
        organism_config=organism_config,
        reproduction_energy_threshold=18.0,
        offspring_energy_cost=5.0,
        seed=seed,
        log_every=5,
    )


# --- interactions -----------------------------------------------------


def test_derive_competition_interactions_from_blocked_pairs() -> None:
    world = SharedGridWorld(SharedGridWorldConfig(width=4, height=4, max_agents=4, max_steps=100))
    world.reset(seed=0)
    world.add_agent(0)
    world.add_agent(1)
    system = require_shared_grid_world_with_spatial_competition(world)
    assert isinstance(system, SpatialCompetition)
    system.last_blocked_pairs = [(0, 1)]
    context = EcologicalContext(experiment_id="e1", seed=0, generation_or_step=1)
    interactions = derive_competition_interactions(system, context)
    assert len(interactions) == 1
    assert interactions[0].actor == 0
    assert interactions[0].target == 1
    assert interactions[0].interaction_type is InteractionType.COMPETITION
    assert interactions[0].outcome is InteractionOutcome.LOSE
    d = interactions[0].to_dict()
    assert d["interaction_type"] == "competition"


def test_derive_resource_acquisition_interactions_only_for_positive_reward() -> None:
    context = EcologicalContext("e1", 0, 1)
    result = derive_resource_acquisition_interactions({0: 3.0, 1: 0.0}, {0: "A", 1: None}, context)
    assert len(result) == 1
    assert result[0].actor == 0
    assert result[0].environmental_consequence == "A"


def test_interaction_network_density_and_diversity() -> None:
    context = EcologicalContext("e1", 0, 1)
    interactions = [
        EcologicalInteraction(
            0, 1, InteractionType.COMPETITION, InteractionOutcome.LOSE, context=context
        ),
        EcologicalInteraction(
            1, 2, InteractionType.COMPETITION, InteractionOutcome.LOSE, context=context
        ),
        EcologicalInteraction(
            2, None, InteractionType.RESOURCE_ACQUISITION, InteractionOutcome.WIN, context=context
        ),
    ]
    network = build_interaction_network(interactions)
    assert network.nodes == {0, 1, 2}
    assert network.degree() == {0: 1, 1: 2, 2: 1}
    density = network.density()
    assert isinstance(density, float)
    assert 0.0 < density <= 1.0
    assert network.interaction_type_diversity() > 0.0


def test_ecological_network_analyzer_insufficient_data() -> None:
    context = EcologicalContext("e1", 0, 1)
    interactions = [
        EcologicalInteraction(
            0, 1, InteractionType.COMPETITION, InteractionOutcome.LOSE, context=context
        )
    ]
    result = EcologicalNetworkAnalyzer().analyze(interactions)
    assert result.structure_analysis_available is False
    assert result.insufficient_data_reason is not None
    assert result.density is None


def test_interaction_turnover_identical_and_disjoint() -> None:
    context = EcologicalContext("e1", 0, 1)
    a = [
        EcologicalInteraction(
            0, 1, InteractionType.COMPETITION, InteractionOutcome.LOSE, context=context
        )
    ]
    assert interaction_turnover(a, a) == 0.0
    b = [
        EcologicalInteraction(
            2, 3, InteractionType.COMPETITION, InteractionOutcome.LOSE, context=context
        )
    ]
    assert interaction_turnover(a, b) == 1.0
    assert interaction_turnover([], []) is None


# --- niches -------------------------------------------------------------


def test_niche_profile_specialist_vs_generalist() -> None:
    specialist = compute_niche_profile(0, ["A", "A", "A", "A"])
    generalist = compute_niche_profile(1, ["A", "B", "A", "B"])
    assert specialist.specialization == 1.0
    assert generalist.specialization == 0.0
    assert generalist.breadth == 1.0
    assert specialist.breadth == 0.0


def test_niche_profile_no_data() -> None:
    profile = compute_niche_profile(0, [])
    assert profile.n_acquisitions == 0
    assert profile.preference_a is None


def test_summarize_population_niches_overlap() -> None:
    profiles = [compute_niche_profile(i, types) for i, types in enumerate([["A"] * 4, ["B"] * 4])]
    summary = summarize_population_niches(profiles)
    assert summary.n_agents_with_data == 2
    assert summary.niche_overlap == 0.0  # maximally divergent preferences


def test_resource_types_from_step_infos_filters_none() -> None:
    infos = [{"resource_type": "A"}, {"resource_type": None}, {"resource_type": "B"}]
    assert resource_types_from_step_infos(infos) == ["A", "B"]


# --- competition ----------------------------------------------------------


def test_gini_coefficient_equal_vs_unequal() -> None:
    assert gini_coefficient([5, 5, 5, 5]) == 0.0
    unequal = gini_coefficient([1, 1, 1, 100])
    assert unequal is not None and unequal > 0.5
    assert gini_coefficient([1]) is None


def test_pielou_evenness_and_herfindahl() -> None:
    even = pielou_evenness([10, 10, 10])
    assert even is not None and abs(even - 1.0) < 1e-9
    uneven = pielou_evenness([1, 1, 100])
    assert uneven is not None and uneven < even
    assert herfindahl_index([10, 10]) == 0.5
    assert herfindahl_index([]) is None


def test_compute_competition_metrics_from_real_run() -> None:
    from genevra.evolution.continuous import ContinuousEvolutionEngine

    engine = ContinuousEvolutionEngine(_make_patch_config(seed=1))
    engine.run()
    metrics = compute_competition_metrics(engine.history, engine.lineage.events())
    assert metrics.population_turnover is not None
    assert metrics.evenness is None or 0.0 <= metrics.evenness <= 1.0
    assert metrics.lineage_survival_fraction is not None


def test_compute_competition_metrics_empty_history() -> None:
    metrics = compute_competition_metrics([], [])
    assert metrics.population_turnover is None
    assert metrics.lineage_survival_fraction is None


# --- spatial / migration ---------------------------------------------------


def test_build_connectivity_regimes() -> None:
    assert build_connectivity(SpatialRegime.FRAGMENTED, 3) == {0: (), 1: (), 2: ()}
    assert build_connectivity(SpatialRegime.CONNECTED, 3)[0] == (1, 2)
    ring = build_connectivity(SpatialRegime.PATCHY, 4)
    assert ring[0] == (3, 1)


def test_metapopulation_migration_moves_individuals() -> None:
    conn = build_connectivity(SpatialRegime.CONNECTED, 2)
    migration = MigrationConfig(migration_probability=1.0, migration_interval=5, connectivity=conn)
    mp = Metapopulation([_make_patch_config(seed=1), _make_patch_config(seed=2)], migration, seed=0)
    history = mp.run(20)
    assert len(history) > 0
    total_migrations = sum(s.migrations_since_last_snapshot for s in history)
    assert total_migrations > 0
    summaries = mp.diversity_by_patch()
    assert len(summaries) == 2


def test_metapopulation_fragmented_never_migrates() -> None:
    conn = build_connectivity(SpatialRegime.FRAGMENTED, 2)
    migration = MigrationConfig(migration_probability=1.0, migration_interval=5, connectivity=conn)
    mp = Metapopulation([_make_patch_config(seed=1), _make_patch_config(seed=2)], migration, seed=0)
    history = mp.run(20)
    assert sum(s.migrations_since_last_snapshot for s in history) == 0


def test_metapopulation_deterministic_given_same_seed() -> None:
    conn = build_connectivity(SpatialRegime.CONNECTED, 2)
    migration = MigrationConfig(migration_probability=0.5, migration_interval=5, connectivity=conn)
    mp1 = Metapopulation([_make_patch_config(1), _make_patch_config(2)], migration, seed=42)
    mp2 = Metapopulation([_make_patch_config(1), _make_patch_config(2)], migration, seed=42)
    h1, h2 = mp1.run(20), mp2.run(20)
    sizes1 = [s.per_patch[0].population_size for s in h1 if 0 in s.per_patch]
    sizes2 = [s.per_patch[0].population_size for s in h2 if 0 in s.per_patch]
    assert sizes1 == sizes2


# --- coevolution ------------------------------------------------------------


def test_coevolution_trajectory_two_species_tracked_separately() -> None:
    engine, trajectory = run_coevolution_experiment(_make_patch_config(seed=3, total_steps=40))
    assert len(trajectory.species_a) > 0
    assert len(trajectory.species_b) > 0
    comparison = CoEvolutionAnalyzer().compare(trajectory)
    assert comparison.final_population_a >= 0
    assert comparison.final_population_b >= 0


# --- roles --------------------------------------------------------------


def test_classify_roles_specialist_generalist_competitor() -> None:
    niche_profiles = {
        0: compute_niche_profile(0, ["A"] * 10),
        1: compute_niche_profile(1, ["A", "B"] * 5),
    }
    context = EcologicalContext("e1", 0, 1)
    interactions = [
        EcologicalInteraction(
            0, 1, InteractionType.COMPETITION, InteractionOutcome.LOSE, context=context
        )
        for _ in range(5)
    ]
    assignments = classify_roles(niche_profiles, interactions)
    roles = {a.agent_id: a.role for a in assignments}
    assert roles[0] in (EcologicalRole.SPECIALIST, EcologicalRole.COMPETITOR)
    assert roles[1] in (EcologicalRole.GENERALIST, EcologicalRole.UNCLASSIFIED)


def test_classify_roles_empty_input() -> None:
    assert classify_roles({}, []) == []


# --- regime transitions ------------------------------------------------


def test_detect_ecological_regime_transitions_labels_direction() -> None:
    rng = np.random.default_rng(0)
    values = [10.0] * 10 + [1.0] * 10
    transitions = detect_ecological_regime_transitions("diversity", values, rng)
    assert len(transitions) >= 1
    assert transitions[0].candidate_label == "diversity_collapse"
    assert transitions[0].confidence == "candidate"


# --- hypotheses -----------------------------------------------------------


def test_all_hypotheses_have_required_fields() -> None:
    assert len(ALL_ECOLOGY_HYPOTHESES) == 5
    for h in ALL_ECOLOGY_HYPOTHESES:
        assert h.null_hypothesis
        assert h.alternative_hypothesis
        assert h.replication_requirement


def test_ecology_hypothesis_insufficient_data() -> None:
    rng = np.random.default_rng(0)
    result = run_ecology_hypothesis_test(
        H1_COMPETITION_CHANGES_LEARNING_STRATEGY, [1.0], [2.0], rng
    )
    assert result.label is AssociationLabel.INSUFFICIENT_DATA
    assert result.p_value is None


def test_ecology_hypothesis_found_association() -> None:
    rng = np.random.default_rng(0)
    sample_a = [0.1, 0.12, 0.11, 0.13]
    sample_b = [0.9, 0.88, 0.91, 0.87]
    result = run_ecology_hypothesis_test(
        H1_COMPETITION_CHANGES_LEARNING_STRATEGY, sample_a, sample_b, rng
    )
    assert result.label is AssociationLabel.ASSOCIATION_FOUND
    assert result.p_value is not None
    assert result.effect_size is not None
