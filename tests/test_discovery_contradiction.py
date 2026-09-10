from genevra.discovery.contradiction import ExperimentCorrelation, find_contradictions
from genevra.discovery.correlation import CorrelationResult


def test_finds_a_contradiction_between_opposite_signed_results() -> None:
    a = ExperimentCorrelation(
        "exp_a", CorrelationResult("x", "y", spearman_rho=0.6, p_value=0.01, n_runs=10)
    )
    b = ExperimentCorrelation(
        "exp_b", CorrelationResult("x", "y", spearman_rho=-0.5, p_value=0.02, n_runs=8)
    )
    contradictions = find_contradictions([a, b])
    assert len(contradictions) == 1
    assert contradictions[0].experiment_a == "exp_a"
    assert contradictions[0].experiment_b == "exp_b"


def test_no_contradiction_when_signs_agree() -> None:
    a = ExperimentCorrelation(
        "exp_a", CorrelationResult("x", "y", spearman_rho=0.6, p_value=0.01, n_runs=10)
    )
    b = ExperimentCorrelation(
        "exp_b", CorrelationResult("x", "y", spearman_rho=0.5, p_value=0.02, n_runs=8)
    )
    assert find_contradictions([a, b]) == []


def test_no_contradiction_when_one_effect_is_too_small() -> None:
    a = ExperimentCorrelation(
        "exp_a", CorrelationResult("x", "y", spearman_rho=0.6, p_value=0.01, n_runs=10)
    )
    b = ExperimentCorrelation(
        "exp_b", CorrelationResult("x", "y", spearman_rho=-0.05, p_value=0.8, n_runs=8)
    )
    assert find_contradictions([a, b], effect_size_threshold=0.2) == []


def test_different_variable_pairs_are_never_compared() -> None:
    a = ExperimentCorrelation(
        "exp_a", CorrelationResult("x", "y", spearman_rho=0.6, p_value=0.01, n_runs=10)
    )
    b = ExperimentCorrelation(
        "exp_b", CorrelationResult("p", "q", spearman_rho=-0.6, p_value=0.01, n_runs=10)
    )
    assert find_contradictions([a, b]) == []
