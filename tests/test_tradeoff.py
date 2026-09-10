from genevra.analysis.tradeoff import TradeoffSample, summarize_tradeoff


def test_missing_measurements_are_reported_as_none_not_zero() -> None:
    samples = [
        TradeoffSample(
            individual_id=i,
            initial_competence=None,
            learning_gain=None,
            eval_shift_fitness=None,
            evolvability_viable_fraction=None,
            evolvability_mean_behavioral_distance=None,
        )
        for i in range(5)
    ]
    result = summarize_tradeoff(samples)
    assert all(value is None for value in result.values())


def test_correlation_detects_a_real_linear_relationship() -> None:
    samples = [
        TradeoffSample(
            individual_id=i,
            initial_competence=float(i),
            learning_gain=float(i) * 2.0,
            eval_shift_fitness=None,
            evolvability_viable_fraction=None,
            evolvability_mean_behavioral_distance=None,
        )
        for i in range(10)
    ]
    result = summarize_tradeoff(samples)
    assert result["initial_competence__vs__learning_gain"] is not None
    assert result["initial_competence__vs__learning_gain"] > 0.99


def test_axes_never_conflated_into_one_score() -> None:
    """The module must never produce a single combined 'intelligence
    score' — only pairwise, independently-inspectable measurements."""
    samples = [
        TradeoffSample(
            individual_id=0,
            initial_competence=1.0,
            learning_gain=2.0,
            eval_shift_fitness=3.0,
            evolvability_viable_fraction=0.5,
            evolvability_mean_behavioral_distance=0.1,
        )
    ]
    result = summarize_tradeoff(samples)
    assert "score" not in "".join(result.keys()).lower()
