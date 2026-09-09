import pytest

matplotlib = pytest.importorskip("matplotlib")
matplotlib.use("Agg")  # headless backend for tests

from genevra import visualization  # noqa: E402

_TRAJECTORY = [
    {
        "generation": g,
        "fitness_summary": {"mean": float(g)},
        "genotypic_diversity": float(g) * 0.5,
        "behavioral_diversity": float(g) * 0.3,
        "mean_novelty": float(g) * 0.2,
        "instantaneous_novelty": float(g) * 0.1,
    }
    for g in range(5)
]


def test_plot_fitness_trajectory_returns_a_figure() -> None:
    fig = visualization.plot_fitness_trajectory(_TRAJECTORY)
    assert fig is not None


def test_plot_novelty_trajectory_returns_a_figure() -> None:
    fig = visualization.plot_novelty_trajectory(_TRAJECTORY)
    assert fig is not None


def test_plot_diversity_trajectory_returns_a_figure() -> None:
    fig = visualization.plot_diversity_trajectory(_TRAJECTORY)
    assert fig is not None


def test_plot_population_size_returns_a_figure() -> None:
    class FakeSnapshot:
        def __init__(self, step: int, size: int) -> None:
            self.step = step
            self.population_size = size

    snapshots = [FakeSnapshot(i * 10, 5 + i) for i in range(4)]
    fig = visualization.plot_population_size(snapshots)
    assert fig is not None


def test_plot_lineage_survival_returns_a_figure() -> None:
    class FakeSummary:
        def __init__(self, size: int) -> None:
            self.size = size

    fig = visualization.plot_lineage_survival([FakeSummary(3), FakeSummary(1), FakeSummary(5)])
    assert fig is not None


def test_plot_evolvability_over_time_returns_a_figure() -> None:
    class FakeReport:
        def __init__(self, distance: float) -> None:
            self.mean_behavioral_distance = distance

    class FakeSample:
        def __init__(self, generation: int, distance: float) -> None:
            self.generation = generation
            self.report = FakeReport(distance)

    samples = [FakeSample(0, 1.0), FakeSample(0, 2.0), FakeSample(5, 3.0)]
    fig = visualization.plot_evolvability_over_time(samples)
    assert fig is not None
