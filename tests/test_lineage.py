import numpy as np
import pytest

from genevra.evolution.lineage import LineageTracker
from genevra.organism.genome import ControllerArchitecture, Genome


def make_genome(seed: int) -> Genome:
    arch = ControllerArchitecture(input_size=4, hidden_size=3, output_size=2)
    return Genome.random(arch, np.random.default_rng(seed))


def test_record_birth_creates_a_retrievable_event() -> None:
    tracker = LineageTracker()
    tracker.record_birth(0, (), generation=0, genome=make_genome(0))
    assert len(tracker) == 1


def test_duplicate_birth_id_raises() -> None:
    tracker = LineageTracker()
    tracker.record_birth(0, (), generation=0, genome=make_genome(0))
    with pytest.raises(ValueError):
        tracker.record_birth(0, (), generation=0, genome=make_genome(0))


def test_death_and_reproduction_are_recorded() -> None:
    tracker = LineageTracker()
    tracker.record_birth(0, (), generation=0, genome=make_genome(0))
    tracker.record_death(0, generation=1)
    tracker.record_reproduction(0)
    [event] = tracker.to_dicts()
    assert event["death_generation"] == 1
    assert event["reproduced"] is True


def test_ancestors_walks_parent_chain() -> None:
    tracker = LineageTracker()
    tracker.record_birth(0, (), generation=0, genome=make_genome(0))
    tracker.record_birth(1, (0,), generation=1, genome=make_genome(1))
    tracker.record_birth(2, (1,), generation=2, genome=make_genome(2))
    assert tracker.ancestors(2) == [1, 0]
    assert tracker.ancestors(0) == []


def test_children_finds_direct_offspring() -> None:
    tracker = LineageTracker()
    tracker.record_birth(0, (), generation=0, genome=make_genome(0))
    tracker.record_birth(1, (0,), generation=1, genome=make_genome(1))
    tracker.record_birth(2, (0,), generation=1, genome=make_genome(2))
    assert sorted(tracker.children(0)) == [1, 2]
    assert tracker.children(1) == []


def test_genome_hash_is_stable_and_distinguishes_genomes() -> None:
    tracker = LineageTracker()
    genome_a = make_genome(0)
    genome_b = make_genome(1)
    tracker.record_birth(0, (), generation=0, genome=genome_a)
    tracker.record_birth(1, (), generation=0, genome=genome_b)
    [event_a] = [e for e in tracker.to_dicts() if e["individual_id"] == 0]
    [event_b] = [e for e in tracker.to_dicts() if e["individual_id"] == 1]
    assert event_a["genome_hash"] != event_b["genome_hash"]

    tracker2 = LineageTracker()
    tracker2.record_birth(0, (), generation=0, genome=genome_a)
    [event_a_again] = tracker2.to_dicts()
    assert event_a_again["genome_hash"] == event_a["genome_hash"]
