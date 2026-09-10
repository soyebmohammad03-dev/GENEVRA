from genevra.discovery.correlation import CorrelationResult
from genevra.discovery.hypothesis import (
    DiscoveryScoreWeights,
    deduplicate_hypotheses,
    discovery_score,
    hypotheses_from_correlations,
    hypotheses_from_recurring_phenomena,
    rank_hypotheses,
)
from genevra.discovery.multiple_testing import FDRResult
from genevra.discovery.phenomena import PhenomenonObservation


def test_hypothesis_generated_for_significant_large_effect() -> None:
    correlation = CorrelationResult(
        variable_a="mutation_sigma",
        variable_b="novelty_auc",
        spearman_rho=0.6,
        p_value=0.01,
        n_runs=10,
    )
    fdr = FDRResult(p_value=0.01, q_value=0.02, significant=True, label="exploratory")
    hypotheses = hypotheses_from_correlations([correlation], [fdr])
    assert len(hypotheses) == 1
    assert hypotheses[0].predicted_direction == "positive"
    assert hypotheses[0].independent_variable == "mutation_sigma"


def test_no_hypothesis_for_insignificant_correlation() -> None:
    correlation = CorrelationResult(
        variable_a="a", variable_b="b", spearman_rho=0.6, p_value=0.2, n_runs=10
    )
    fdr = FDRResult(p_value=0.2, q_value=0.3, significant=False, label="exploratory")
    assert hypotheses_from_correlations([correlation], [fdr]) == []


def test_no_hypothesis_for_small_effect_size_even_if_significant() -> None:
    correlation = CorrelationResult(
        variable_a="a", variable_b="b", spearman_rho=0.05, p_value=0.001, n_runs=50
    )
    fdr = FDRResult(p_value=0.001, q_value=0.001, significant=True, label="exploratory")
    hypotheses = hypotheses_from_correlations([correlation], [fdr], effect_size_threshold=0.3)
    assert hypotheses == []


def test_recurring_phenomena_require_minimum_seed_count() -> None:
    observations = [
        PhenomenonObservation(
            name="novelty_without_fitness_gain",
            description="d",
            experiment="exp",
            seed=seed,
            evidence={},
        )
        for seed in (0, 1)
    ]
    hypotheses = hypotheses_from_recurring_phenomena(observations, min_seed_count=3)
    assert hypotheses == []
    hypotheses = hypotheses_from_recurring_phenomena(observations, min_seed_count=2)
    assert len(hypotheses) == 1


def test_discovery_score_increases_with_effect_reproducibility_and_certainty() -> None:
    low = discovery_score(
        effect_magnitude=0.1, n_independent_seeds=1, q_value=0.5, coverage_fraction=0.1
    )
    high = discovery_score(
        effect_magnitude=0.9, n_independent_seeds=10, q_value=0.001, coverage_fraction=1.0
    )
    assert high > low
    assert 0.0 <= low <= 1.0
    assert 0.0 <= high <= 1.0


def test_discovery_score_weights_sum_to_one_by_convention() -> None:
    weights = DiscoveryScoreWeights()
    total = (
        weights.effect_magnitude + weights.reproducibility + weights.certainty + weights.coverage
    )
    assert abs(total - 1.0) < 1e-9


def test_rank_hypotheses_sorts_by_evidence_score_descending() -> None:
    correlation_low = CorrelationResult("a", "b", spearman_rho=0.31, p_value=0.01, n_runs=5)
    correlation_high = CorrelationResult("c", "d", spearman_rho=0.9, p_value=0.001, n_runs=5)
    fdr = FDRResult(p_value=0.01, q_value=0.01, significant=True, label="exploratory")
    hypotheses = hypotheses_from_correlations([correlation_low, correlation_high], [fdr, fdr])
    ranked = rank_hypotheses(hypotheses)
    assert ranked[0].evidence_score >= ranked[1].evidence_score


def test_deduplicate_hypotheses_keeps_first_occurrence() -> None:
    correlation = CorrelationResult("a", "b", spearman_rho=0.6, p_value=0.01, n_runs=5)
    fdr = FDRResult(p_value=0.01, q_value=0.01, significant=True, label="exploratory")
    hypotheses = hypotheses_from_correlations([correlation, correlation], [fdr, fdr])
    deduped = deduplicate_hypotheses(hypotheses)
    assert len(deduped) == 1
