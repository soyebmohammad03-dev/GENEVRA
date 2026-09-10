import numpy as np
import pytest

from genevra.analysis.learning_strategy import LearningStrategy
from genevra.analysis.strategy_clustering import (
    KMeansClusterer,
    select_k,
    strategy_frequencies,
    strategy_lineage_survival,
    strategy_turnover,
)
from genevra.evolution.lineage import LineageEvent
from genevra.organism.genome import ControllerArchitecture, Genome


def _genome(learning_genes: tuple[float, float, float]) -> Genome:
    arch = ControllerArchitecture(input_size=4, hidden_size=3, output_size=2)
    genome = Genome.random(arch, np.random.default_rng(0))
    genome.learning_genes[:] = learning_genes
    return genome


def _two_well_separated_clusters() -> list[LearningStrategy]:
    rng = np.random.default_rng(1)
    cluster_a = [
        LearningStrategy(learning_rate=0.01 + rng.normal(0, 0.001), plasticity_gate=0.9, decay=0.0)
        for _ in range(15)
    ]
    cluster_b = [
        LearningStrategy(learning_rate=0.5 + rng.normal(0, 0.001), plasticity_gate=0.1, decay=0.0)
        for _ in range(15)
    ]
    return cluster_a + cluster_b


def test_kmeans_recovers_two_known_clusters_deterministically() -> None:
    strategies = _two_well_separated_clusters()
    clusterer = KMeansClusterer(k=2)
    assignment_1 = clusterer.fit(strategies, np.random.default_rng(42))
    assignment_2 = clusterer.fit(strategies, np.random.default_rng(42))
    assert assignment_1.labels == assignment_2.labels

    first_half_labels = set(assignment_1.labels[:15])
    second_half_labels = set(assignment_1.labels[15:])
    assert first_half_labels != second_half_labels
    assert len(first_half_labels) == 1
    assert len(second_half_labels) == 1


def test_select_k_prefers_two_clusters_for_bimodal_data() -> None:
    strategies = _two_well_separated_clusters()
    assignment = select_k(strategies, np.random.default_rng(0), k_candidates=(1, 2, 3, 4))
    assert assignment.k == 2


def test_strategy_frequencies_sum_to_one() -> None:
    strategies = _two_well_separated_clusters()
    assignment = KMeansClusterer(k=2).fit(strategies, np.random.default_rng(0))
    frequencies = strategy_frequencies(assignment)
    assert np.isclose(sum(frequencies.values()), 1.0)


def _lineage_event(individual_id: int, generation: int, learning_rate: float) -> LineageEvent:
    return LineageEvent(
        individual_id=individual_id,
        parent_ids=(),
        generation=generation,
        genome_hash="deadbeef",
        reproduced=True,
        learning_strategy=(learning_rate, 0.9, 0.0),
    )


def test_strategy_lineage_survival_groups_by_cluster() -> None:
    events = [_lineage_event(i, 0, 0.01) for i in range(5)] + [
        _lineage_event(i, 0, 0.5) for i in range(5, 10)
    ]
    summary = strategy_lineage_survival(events, KMeansClusterer(k=2), np.random.default_rng(0))
    assert len(summary) == 2
    assert sum(s.num_individuals for s in summary) == 10


def test_strategy_turnover_is_zero_when_dominant_strategy_persists() -> None:
    gen0 = [_lineage_event(i, 0, 0.01) for i in range(10)]
    gen1 = [_lineage_event(i, 1, 0.01) for i in range(10, 20)]
    turnover = strategy_turnover([gen0, gen1], KMeansClusterer(k=1), np.random.default_rng(0))
    assert turnover == [0.0]


def test_strategy_turnover_detects_a_full_switch() -> None:
    gen0 = [_lineage_event(i, 0, 0.01) for i in range(10)]
    gen1 = [_lineage_event(i, 1, 0.9) for i in range(10, 20)]
    turnover = strategy_turnover([gen0, gen1], KMeansClusterer(k=2), np.random.default_rng(0))
    assert turnover[0] == 1.0


def test_lineage_tracker_records_learning_strategy_at_birth() -> None:
    from genevra.evolution.lineage import LineageTracker

    tracker = LineageTracker()
    genome = _genome((0.05, 1.0, 0.0))
    tracker.record_birth(0, (), 0, genome)
    event = tracker.events()[0]
    assert event.learning_strategy == pytest.approx((0.05, 1.0, 0.0))
