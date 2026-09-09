import numpy as np

from genevra.analysis.lineage_analysis import (
    dominant_lineage,
    lineage_diversity,
    summarize_lineages,
)
from genevra.evolution.lineage import LineageTracker
from genevra.organism.genome import ControllerArchitecture, Genome


def make_genome(seed: int) -> Genome:
    return Genome.random(ControllerArchitecture(4, 3, 2), np.random.default_rng(seed))


def test_summarize_lineages_groups_by_founder() -> None:
    tracker = LineageTracker()
    tracker.record_birth(0, (), generation=0, genome=make_genome(0))
    tracker.record_birth(1, (0,), generation=1, genome=make_genome(1))
    tracker.record_birth(2, (1,), generation=2, genome=make_genome(2))
    tracker.record_birth(3, (), generation=0, genome=make_genome(3))

    summaries = summarize_lineages(tracker)
    by_founder = {s.founder_id: s for s in summaries}
    assert by_founder[0].size == 3
    assert by_founder[3].size == 1
    assert by_founder[0].max_generation_reached == 2


def test_still_alive_and_extinction_generation() -> None:
    tracker = LineageTracker()
    tracker.record_birth(0, (), generation=0, genome=make_genome(0))
    tracker.record_birth(1, (0,), generation=1, genome=make_genome(1))
    tracker.record_death(0, generation=1)
    tracker.record_death(1, generation=3)

    summaries = summarize_lineages(tracker)
    [summary] = summaries
    assert summary.still_alive is False
    assert summary.extinction_generation == 3


def test_lineage_stays_alive_if_any_member_has_no_death_recorded() -> None:
    tracker = LineageTracker()
    tracker.record_birth(0, (), generation=0, genome=make_genome(0))
    tracker.record_birth(1, (0,), generation=1, genome=make_genome(1))
    tracker.record_death(0, generation=1)
    # individual 1 never recorded as dead

    [summary] = summarize_lineages(tracker)
    assert summary.still_alive is True
    assert summary.extinction_generation is None


def test_dominant_lineage_is_the_largest() -> None:
    tracker = LineageTracker()
    tracker.record_birth(0, (), generation=0, genome=make_genome(0))
    tracker.record_birth(1, (0,), generation=1, genome=make_genome(1))
    tracker.record_birth(2, (1,), generation=2, genome=make_genome(2))
    tracker.record_birth(3, (), generation=0, genome=make_genome(3))

    summaries = summarize_lineages(tracker)
    dominant = dominant_lineage(summaries)
    assert dominant is not None
    assert dominant.founder_id == 0


def test_dominant_lineage_of_empty_summaries_is_none() -> None:
    assert dominant_lineage([]) is None


def test_lineage_diversity_is_zero_for_total_dominance() -> None:
    tracker = LineageTracker()
    for i in range(5):
        tracker.record_birth(i, (0,) if i > 0 else (), generation=i, genome=make_genome(i))
    summaries = summarize_lineages(tracker)
    assert lineage_diversity(summaries) == 0.0  # only one lineage


def test_lineage_diversity_is_one_for_perfectly_even_lineages() -> None:
    tracker = LineageTracker()
    for i in range(4):
        tracker.record_birth(i, (), generation=0, genome=make_genome(i))
    summaries = summarize_lineages(tracker)
    assert lineage_diversity(summaries) == 1.0  # 4 equally-sized (size=1) lineages
