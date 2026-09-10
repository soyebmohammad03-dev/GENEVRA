from genevra.discovery.anomaly import detect_anomalies, robust_z_scores, trajectory_metric_series


def test_robust_z_scores_flags_an_obvious_outlier() -> None:
    values = [1.0] * 20 + [100.0]
    scores = robust_z_scores(values)
    assert abs(scores[-1]) > abs(scores[0])


def test_constant_series_has_zero_z_scores() -> None:
    assert robust_z_scores([5.0] * 10) == [0.0] * 10


def test_detect_anomalies_finds_the_spike_generation() -> None:
    values = [1.0] * 15 + [50.0] + [1.0] * 15
    anomalies = detect_anomalies({"metric": values}, "exp", seed=0)
    assert len(anomalies) == 1
    assert anomalies[0].generation == 15
    assert anomalies[0].experiment == "exp"
    assert anomalies[0].seed == 0


def test_detect_anomalies_empty_for_flat_series() -> None:
    assert detect_anomalies({"metric": [1.0] * 20}, "exp", seed=0) == []


def test_trajectory_metric_series_extracts_nested_keys() -> None:
    trajectory = [{"fitness_summary": {"mean": 1.0}}, {"fitness_summary": {"mean": 2.0}}]
    series = trajectory_metric_series(trajectory, ["fitness_summary.mean"])
    assert series["fitness_summary.mean"] == [1.0, 2.0]
