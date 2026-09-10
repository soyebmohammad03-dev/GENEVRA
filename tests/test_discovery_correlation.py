import numpy as np
import pytest

from genevra.discovery.correlation import RunSummary, correlation_discovery, spearman_rho
from genevra.discovery.multiple_testing import benjamini_hochberg


def test_spearman_rho_is_one_for_a_monotonic_relationship() -> None:
    x = [1, 2, 3, 4, 5]
    y = [10, 20, 30, 40, 50]
    assert spearman_rho(x, y) == pytest.approx(1.0)


def test_spearman_rho_is_near_zero_for_unrelated_data() -> None:
    rng = np.random.default_rng(0)
    x = rng.normal(size=200)
    y = rng.normal(size=200)
    assert abs(spearman_rho(x, y)) < 0.2


def _runs(n: int, rng: np.random.Generator) -> list[RunSummary]:
    runs = []
    for i in range(n):
        x = float(i)
        y = x * 2.0 + float(rng.normal(0, 0.01))
        runs.append(RunSummary(experiment="exp", seed=i, variables={"x": x, "y": y}))
    return runs


def test_correlation_discovery_recovers_a_strong_relationship() -> None:
    rng = np.random.default_rng(0)
    runs = _runs(12, rng)
    results = correlation_discovery(runs, [("x", "y")], rng, num_permutations=200)
    assert len(results) == 1
    assert results[0].spearman_rho > 0.9
    assert results[0].p_value < 0.05
    assert results[0].n_runs == 12


def test_correlation_discovery_respects_the_unit_of_analysis() -> None:
    rng = np.random.default_rng(0)
    runs = _runs(12, rng)
    results = correlation_discovery(runs, [("x", "y")], rng, num_permutations=50)
    assert results[0].unit_of_analysis == "one (experiment, seed) run per observation"


def test_correlation_discovery_excludes_runs_missing_a_variable() -> None:
    rng = np.random.default_rng(0)
    runs = _runs(5, rng) + [RunSummary(experiment="exp", seed=99, variables={"x": 1.0})]
    results = correlation_discovery(runs, [("x", "y")], rng, num_permutations=50)
    assert results[0].n_runs == 5


def test_multiple_testing_correction_reduces_false_positives_among_many_pairs() -> None:
    rng = np.random.default_rng(1)
    variables = [f"v{i}" for i in range(15)]
    runs = [
        RunSummary(experiment="exp", seed=i, variables={v: float(rng.normal()) for v in variables})
        for i in range(10)
    ]
    from genevra.discovery.hypothesis import _pairwise

    pairs = _pairwise(variables)
    results = correlation_discovery(runs, pairs, rng, num_permutations=200)
    fdr = benjamini_hochberg([r.p_value for r in results])
    raw_significant = sum(1 for r in results if r.p_value < 0.05)
    fdr_significant = sum(1 for f in fdr if f.significant)
    assert fdr_significant <= raw_significant
