from genevra.discovery.phenomena import (
    DiversityCollapseWithContinuedNoveltyRule,
    NoveltyWithoutFitnessGainRule,
    PhenomenonDetector,
    RepeatedRegimeRule,
)


def _gen(generation: int, fitness_mean: float, novelty: float, diversity: float) -> dict:
    return {
        "generation": generation,
        "fitness_summary": {"mean": fitness_mean},
        "instantaneous_novelty": novelty,
        "genotypic_diversity": diversity,
    }


def test_novelty_without_fitness_gain_is_detected() -> None:
    trajectory = [_gen(g, 1.0, 0.1 + g * 0.05, 0.5) for g in range(10)]
    observations = NoveltyWithoutFitnessGainRule().detect(trajectory, "exp", 0)
    assert len(observations) == 1
    assert observations[0].name == "novelty_without_fitness_gain"


def test_novelty_without_fitness_gain_is_absent_when_fitness_also_rises() -> None:
    trajectory = [_gen(g, 1.0 + g * 0.5, 0.1 + g * 0.05, 0.5) for g in range(10)]
    assert NoveltyWithoutFitnessGainRule().detect(trajectory, "exp", 0) == []


def test_diversity_collapse_with_continued_novelty_is_detected() -> None:
    trajectory = [_gen(g, 1.0, 0.1 + g * 0.01, 1.0 - g * 0.05) for g in range(10)]
    observations = DiversityCollapseWithContinuedNoveltyRule().detect(trajectory, "exp", 0)
    assert len(observations) == 1


def test_repeated_regime_rule_needs_enough_generations() -> None:
    trajectory = [_gen(g, 1.0, 0.1, 0.5) for g in range(4)]
    assert RepeatedRegimeRule(window=5).detect(trajectory, "exp", 0) == []


def test_detector_aggregates_across_rules() -> None:
    trajectory = [_gen(g, 1.0, 0.1 + g * 0.05, 1.0 - g * 0.05) for g in range(10)]
    detector = PhenomenonDetector(
        [NoveltyWithoutFitnessGainRule(), DiversityCollapseWithContinuedNoveltyRule()]
    )
    observations = detector.detect(trajectory, "exp", 0)
    names = {o.name for o in observations}
    assert names == {"novelty_without_fitness_gain", "diversity_collapse_with_continued_novelty"}


def test_detector_rejects_empty_rule_list() -> None:
    import pytest

    with pytest.raises(ValueError):
        PhenomenonDetector([])
