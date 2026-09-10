import numpy as np

from genevra.discovery.hypothesis import Hypothesis
from genevra.discovery.loop import evaluate_hypothesis, run_hypothesis_loop
from genevra.discovery.replication import EvidenceSet, ReplicationRunner


def _hypothesis(predicted_direction: str | None = "positive") -> Hypothesis:
    return Hypothesis(
        hypothesis_id="h1",
        statement="stmt",
        independent_variable="x",
        dependent_variable="y",
        predicted_direction=predicted_direction,
        supporting_observations=(),
        conflicting_observations=(),
        source_experiment_ids=(),
        evidence_score=0.5,
    )


def test_no_replication_evidence_is_insufficient() -> None:
    evaluation = evaluate_hypothesis(_hypothesis(), None)
    assert evaluation.label == "insufficient_evidence"


def test_too_few_seeds_is_insufficient() -> None:
    original = EvidenceSet(seeds=(0,), values=(1.0,), source="original")
    replication = EvidenceSet(seeds=(1, 2), values=(1.0, 1.1), source="replication")
    result = ReplicationRunner().evaluate("h1", original, replication, np.random.default_rng(0))
    evaluation = evaluate_hypothesis(_hypothesis(), result, min_independent_seeds=3)
    assert evaluation.label == "insufficient_evidence"


def test_matching_direction_is_supported() -> None:
    original = EvidenceSet(seeds=(0,), values=(1.0,), source="original")
    replication = EvidenceSet(
        seeds=(1, 2, 3, 4), values=(1.0, 1.1, 0.95, 1.05), source="replication"
    )
    result = ReplicationRunner().evaluate("h1", original, replication, np.random.default_rng(0))
    evaluation = evaluate_hypothesis(_hypothesis("positive"), result, min_independent_seeds=3)
    assert evaluation.label == "supported"


def test_opposite_direction_is_contradicted() -> None:
    original = EvidenceSet(seeds=(0,), values=(1.0,), source="original")
    replication = EvidenceSet(
        seeds=(1, 2, 3, 4), values=(1.0, 1.1, 0.95, 1.05), source="replication"
    )
    result = ReplicationRunner().evaluate("h1", original, replication, np.random.default_rng(0))
    evaluation = evaluate_hypothesis(_hypothesis("negative"), result, min_independent_seeds=3)
    assert evaluation.label == "contradicted"


def test_ci_including_zero_is_inconclusive() -> None:
    original = EvidenceSet(seeds=(0,), values=(1.0,), source="original")
    replication = EvidenceSet(
        seeds=(1, 2, 3, 4), values=(0.5, -0.4, 0.3, -0.2), source="replication"
    )
    result = ReplicationRunner().evaluate("h1", original, replication, np.random.default_rng(0))
    evaluation = evaluate_hypothesis(_hypothesis("positive"), result, min_independent_seeds=3)
    assert evaluation.label == "inconclusive"


def test_run_hypothesis_loop_ties_collectors_to_evaluations() -> None:
    def original_collector(hypothesis: Hypothesis, seeds: tuple[int, ...]) -> tuple[float, ...]:
        return tuple(1.0 for _ in seeds)

    def replication_collector(hypothesis: Hypothesis, seeds: tuple[int, ...]) -> tuple[float, ...]:
        return tuple(1.0 + 0.01 * i for i in range(len(seeds)))

    evaluations = run_hypothesis_loop(
        [_hypothesis("positive")],
        original_collector,
        replication_collector,
        original_seeds=(0, 1),
        replication_seeds=(100, 101, 102, 103),
        rng=np.random.default_rng(0),
    )
    assert len(evaluations) == 1
    assert evaluations[0].hypothesis_id == "h1"


def test_run_hypothesis_loop_rejects_overlapping_seed_pools() -> None:
    import pytest

    def collector(hypothesis: Hypothesis, seeds: tuple[int, ...]) -> tuple[float, ...]:
        return tuple(1.0 for _ in seeds)

    with pytest.raises(ValueError):
        run_hypothesis_loop(
            [_hypothesis()],
            collector,
            collector,
            original_seeds=(0, 1),
            replication_seeds=(1, 2),
            rng=np.random.default_rng(0),
        )
