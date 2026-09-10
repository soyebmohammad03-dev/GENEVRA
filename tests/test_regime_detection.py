import numpy as np

from genevra.analysis.regime_detection import (
    ChangePointConfig,
    detect_change_points,
    detect_regime_transitions,
)


def test_no_change_point_in_a_flat_series() -> None:
    values = list(np.random.default_rng(0).normal(0, 0.01, 40))
    change_points = detect_change_points(
        values, "metric", np.random.default_rng(0), config=ChangePointConfig(num_permutations=200)
    )
    assert change_points == []


def test_detects_a_single_obvious_shift() -> None:
    values = [0.0] * 20 + [10.0] * 20
    change_points = detect_change_points(
        values, "metric", np.random.default_rng(0), config=ChangePointConfig(num_permutations=200)
    )
    assert len(change_points) == 1
    assert 15 <= change_points[0].index <= 25
    assert change_points[0].magnitude > 0


def test_change_point_index_matches_supplied_generations() -> None:
    generations = list(range(100, 140))
    values = [0.0] * 20 + [10.0] * 20
    change_points = detect_change_points(
        values,
        "metric",
        np.random.default_rng(0),
        generations=generations,
        config=ChangePointConfig(num_permutations=200),
    )
    assert change_points[0].generation == generations[change_points[0].index]


def test_detection_is_deterministic_given_the_same_rng_seed() -> None:
    values = [0.0] * 15 + [5.0] * 15 + [1.0] * 15
    first = detect_change_points(
        values, "metric", np.random.default_rng(7), config=ChangePointConfig(num_permutations=150)
    )
    second = detect_change_points(
        values, "metric", np.random.default_rng(7), config=ChangePointConfig(num_permutations=150)
    )
    assert [cp.index for cp in first] == [cp.index for cp in second]


def test_regime_transitions_label_novelty_increase_as_burst() -> None:
    series = {"instantaneous_novelty": [0.1] * 20 + [0.9] * 20}
    records = detect_regime_transitions(
        series,
        experiment="exp1",
        seed=0,
        rng=np.random.default_rng(0),
        config=ChangePointConfig(num_permutations=200),
    )
    assert len(records) == 1
    assert records[0].transition_type == "novelty_burst"
    assert records[0].experiment == "exp1"
    assert records[0].seed == 0


def test_regime_transitions_label_diversity_decrease_as_collapse() -> None:
    series = {"genotypic_diversity": [1.0] * 20 + [0.05] * 20}
    records = detect_regime_transitions(
        series,
        experiment="exp1",
        seed=0,
        rng=np.random.default_rng(0),
        config=ChangePointConfig(num_permutations=200),
    )
    assert records[0].transition_type == "diversity_collapse"


def test_unrecognized_metric_falls_back_to_generic_label() -> None:
    series = {"custom_metric": [0.0] * 20 + [5.0] * 20}
    records = detect_regime_transitions(
        series,
        experiment="exp1",
        seed=0,
        rng=np.random.default_rng(0),
        config=ChangePointConfig(num_permutations=200),
    )
    assert records[0].transition_type == "regime_change"


def test_records_carry_a_non_causal_disclaimer() -> None:
    series = {"instantaneous_novelty": [0.1] * 20 + [0.9] * 20}
    records = detect_regime_transitions(
        series,
        experiment="exp1",
        seed=0,
        rng=np.random.default_rng(0),
        config=ChangePointConfig(num_permutations=200),
    )
    assert "not causally validated" in records[0].note.lower()
