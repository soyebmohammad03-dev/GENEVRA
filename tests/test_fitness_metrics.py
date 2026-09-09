from genevra.metrics.fitness_metrics import compute_fitness_summary


def test_summary_of_empty_scores_is_all_zero() -> None:
    summary = compute_fitness_summary([])
    assert summary.n == 0
    assert summary.mean == 0.0
    assert summary.max == 0.0


def test_summary_matches_known_values() -> None:
    scores = [1.0, 2.0, 3.0, 4.0]
    summary = compute_fitness_summary(scores)
    assert summary.n == 4
    assert summary.mean == 2.5
    assert summary.median == 2.5
    assert summary.max == 4.0
    assert summary.min == 1.0
    assert summary.std > 0.0


def test_summary_of_single_value_has_zero_std() -> None:
    summary = compute_fitness_summary([5.0])
    assert summary.std == 0.0
    assert summary.mean == 5.0
