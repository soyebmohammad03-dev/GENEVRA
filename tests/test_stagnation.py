from genevra.analysis.stagnation import StagnationAnalyzer, StagnationConfig


def make_generation(
    generation: int, novelty: float, genotypic: float, behavioral: float, fitness_mean: float
) -> dict:
    return {
        "generation": generation,
        "instantaneous_novelty": novelty,
        "genotypic_diversity": genotypic,
        "behavioral_diversity": behavioral,
        "fitness_summary": {"mean": fitness_mean},
    }


def test_fitness_plateau_alone_never_triggers_stagnation_signals() -> None:
    """A flat fitness trajectory with rising diversity/novelty must NOT be
    reported as a contributing stagnation signal — this is the central
    scientific-integrity requirement for this module."""
    trajectory = [
        make_generation(
            g, novelty=g * 1.0, genotypic=g * 0.5, behavioral=g * 0.5, fitness_mean=10.0
        )
        for g in range(6)
    ]
    report = StagnationAnalyzer().analyze(trajectory)
    assert report.fitness_plateaued is True
    assert "fitness_plateau" not in report.contributing_signals
    assert "fitness" not in " ".join(report.contributing_signals)
    assert report.stagnation_score == 0.0


def test_declining_novelty_and_diversity_are_detected() -> None:
    trajectory = [
        make_generation(
            g, novelty=10.0 - g, genotypic=10.0 - g, behavioral=10.0 - g, fitness_mean=float(g)
        )
        for g in range(6)
    ]
    report = StagnationAnalyzer().analyze(trajectory)
    assert "declining_novelty" in report.contributing_signals
    assert "declining_genotypic_diversity" in report.contributing_signals
    assert "declining_behavioral_diversity" in report.contributing_signals
    assert report.stagnation_score == 1.0
    assert report.detected_at_generation == 5


def test_rising_signals_are_never_flagged_as_declining() -> None:
    trajectory = [
        make_generation(
            g, novelty=float(g), genotypic=float(g), behavioral=float(g), fitness_mean=float(g)
        )
        for g in range(6)
    ]
    report = StagnationAnalyzer().analyze(trajectory)
    assert report.contributing_signals == ()
    assert report.stagnation_score == 0.0
    assert report.detected_at_generation is None


def test_short_trajectory_below_window_does_not_crash() -> None:
    trajectory = [make_generation(0, novelty=1.0, genotypic=1.0, behavioral=1.0, fitness_mean=1.0)]
    report = StagnationAnalyzer(StagnationConfig(window=5)).analyze(trajectory)
    assert report.stagnation_score == 0.0
    assert report.signals_evaluated == ()


def test_thresholds_are_explicit_configuration_not_hidden_constants() -> None:
    config = StagnationConfig(
        novelty_decline_threshold=-100.0,  # effectively impossible to trigger
        genotypic_diversity_decline_threshold=-100.0,
        behavioral_diversity_decline_threshold=-100.0,
    )
    trajectory = [
        make_generation(
            g, novelty=10.0 - g, genotypic=10.0 - g, behavioral=10.0 - g, fitness_mean=float(g)
        )
        for g in range(6)
    ]
    report = StagnationAnalyzer(config).analyze(trajectory)
    assert report.contributing_signals == ()  # thresholds made it impossible to trigger


def test_evolvability_trend_is_an_optional_extra_signal() -> None:
    trajectory = [
        make_generation(
            g, novelty=float(g), genotypic=float(g), behavioral=float(g), fitness_mean=float(g)
        )
        for g in range(6)
    ]
    declining_evolvability = [10.0, 8.0, 6.0, 4.0, 2.0]
    report_without = StagnationAnalyzer().analyze(trajectory)
    report_with = StagnationAnalyzer().analyze(
        trajectory, evolvability_trend=declining_evolvability
    )
    assert "declining_evolvability" not in report_without.signals_evaluated
    assert "declining_evolvability" in report_with.signals_evaluated
    assert "declining_evolvability" in report_with.contributing_signals


def test_min_signal_fraction_controls_detection_sensitivity() -> None:
    # Only novelty declines; diversity signals rise.
    trajectory = [
        make_generation(
            g, novelty=10.0 - g, genotypic=float(g), behavioral=float(g), fitness_mean=float(g)
        )
        for g in range(6)
    ]
    lenient = StagnationAnalyzer(StagnationConfig(min_signal_fraction_to_detect=0.2)).analyze(
        trajectory
    )
    strict = StagnationAnalyzer(StagnationConfig(min_signal_fraction_to_detect=0.9)).analyze(
        trajectory
    )
    assert lenient.detected_at_generation is not None
    assert strict.detected_at_generation is None
