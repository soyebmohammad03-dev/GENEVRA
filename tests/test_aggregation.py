import numpy as np
import pytest

from genevra.analysis.aggregation import (
    aggregate_metric_across_runs,
    area_under_trajectory,
    bootstrap_confidence_interval,
    cohens_d,
    final_generation_values,
    permutation_test,
)


def _extract(entry: dict) -> float:
    return float(entry["value"])


def test_aggregate_handles_equal_length_trajectories() -> None:
    trajectories = [
        [{"value": 1.0}, {"value": 2.0}, {"value": 3.0}],
        [{"value": 3.0}, {"value": 4.0}, {"value": 5.0}],
    ]
    aggregates = aggregate_metric_across_runs(trajectories, _extract)
    assert len(aggregates) == 3
    assert aggregates[0].mean == 2.0
    assert all(a.n_runs == 2 for a in aggregates)


def test_aggregate_handles_unequal_length_trajectories_without_padding() -> None:
    trajectories = [
        [{"value": 1.0}, {"value": 2.0}, {"value": 3.0}],  # extinct early -> shorter
        [{"value": 1.0}],
    ]
    aggregates = aggregate_metric_across_runs(trajectories, _extract)
    assert len(aggregates) == 3
    assert aggregates[0].n_runs == 2
    assert aggregates[1].n_runs == 1
    assert aggregates[2].n_runs == 1


def test_aggregate_of_empty_trajectories_is_empty() -> None:
    assert aggregate_metric_across_runs([], _extract) == []
    assert aggregate_metric_across_runs([[], []], _extract) == []


def test_final_generation_values_uses_actual_last_generation() -> None:
    trajectories = [
        [{"value": 1.0}, {"value": 9.0}],
        [{"value": 5.0}],  # shorter run, last value still used
        [],  # completely failed run: excluded, not padded
    ]
    values = final_generation_values(trajectories, _extract)
    assert values == [9.0, 5.0]


def test_area_under_trajectory_of_constant_values() -> None:
    assert area_under_trajectory([2.0, 2.0, 2.0, 2.0]) == pytest.approx(6.0)


def test_area_under_trajectory_degenerate_cases() -> None:
    assert area_under_trajectory([]) == 0.0
    assert area_under_trajectory([5.0]) == 0.0


def test_permutation_test_detects_a_real_difference() -> None:
    rng = np.random.default_rng(0)
    sample_a = [10.0, 11.0, 9.0, 10.5, 10.2]
    sample_b = [1.0, 2.0, 0.5, 1.5, 1.2]
    result = permutation_test(sample_a, sample_b, rng, num_permutations=500)
    assert result.observed_difference > 0
    assert result.p_value < 0.05


def test_permutation_test_does_not_detect_difference_in_identical_samples() -> None:
    rng = np.random.default_rng(0)
    sample = [1.0, 2.0, 3.0, 4.0, 5.0]
    result = permutation_test(sample, list(sample), rng, num_permutations=500)
    assert result.observed_difference == 0.0
    assert result.p_value == 1.0  # every permutation is at least as extreme as "no difference"


def test_permutation_test_p_value_never_exactly_zero() -> None:
    rng = np.random.default_rng(0)
    result = permutation_test([100.0] * 5, [-100.0] * 5, rng, num_permutations=200)
    assert result.p_value > 0.0


def test_permutation_test_rejects_empty_sample() -> None:
    rng = np.random.default_rng(0)
    with pytest.raises(ValueError):
        permutation_test([], [1.0], rng)


def test_cohens_d_zero_for_identical_distributions() -> None:
    result = cohens_d([1.0, 2.0, 3.0, 4.0], [1.0, 2.0, 3.0, 4.0])
    assert result.cohens_d == 0.0
    assert result.mean_difference == 0.0


def test_cohens_d_large_for_clearly_separated_samples() -> None:
    result = cohens_d([10.0, 10.1, 9.9, 10.05], [0.0, 0.1, -0.1, 0.05])
    assert result.cohens_d > 5.0  # a huge, obvious effect
    assert result.n_a == 4
    assert result.n_b == 4


def test_cohens_d_rejects_too_small_samples() -> None:
    with pytest.raises(ValueError):
        cohens_d([1.0], [1.0, 2.0])


def test_bootstrap_ci_contains_the_true_mean_for_a_known_distribution() -> None:
    rng = np.random.default_rng(0)
    sample = rng.normal(loc=5.0, scale=1.0, size=200)
    ci = bootstrap_confidence_interval(sample, rng, confidence_level=0.95, n_resamples=1000)
    assert ci.low < ci.point_estimate < ci.high
    assert ci.low < 5.0 < ci.high  # true mean should fall inside a 95% CI from n=200


def test_bootstrap_ci_narrows_as_confidence_level_decreases() -> None:
    rng = np.random.default_rng(0)
    sample = list(rng.normal(loc=0.0, scale=2.0, size=100))
    wide = bootstrap_confidence_interval(sample, np.random.default_rng(1), confidence_level=0.99)
    narrow = bootstrap_confidence_interval(sample, np.random.default_rng(1), confidence_level=0.80)
    assert (wide.high - wide.low) > (narrow.high - narrow.low)


def test_bootstrap_ci_rejects_too_small_samples() -> None:
    with pytest.raises(ValueError):
        bootstrap_confidence_interval([1.0], np.random.default_rng(0))
