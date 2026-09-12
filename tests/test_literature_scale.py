from __future__ import annotations

import numpy as np
import pytest

from genevra.literature.boundary_search import run_boundary_sweep
from genevra.literature.cases import case_a_plasticity_evolvability_tradeoff
from genevra.literature.claims import LiteratureClaim
from genevra.literature.comparison_matrix import (
    COMPARISON_MATRIX_COLUMNS,
    ComparisonRow,
    build_comparison_matrix,
    comparison_matrix_csv,
    comparison_matrix_markdown,
)
from genevra.literature.falsification import (
    generate_falsification_experiments,
    generate_falsification_hypotheses,
    rank_falsification_experiments,
)
from genevra.literature.quality_levels import (
    ReproductionQualityLevel,
    classify_quality_level_across_regimes,
    classify_single_result,
)
from genevra.literature.runner import (
    LiteratureReproductionRunner,
    ReproductionLabel,
    ReproductionResult,
)


def _tiny_result(label: ReproductionLabel, cohens_d: float | None = None) -> ReproductionResult:
    from genevra.analysis.aggregation import EffectSizeResult, PermutationTestResult
    from genevra.analysis.comparison import ComparisonValidation

    effect = (
        EffectSizeResult(cohens_d=cohens_d, mean_difference=1.0, pooled_std=1.0, n_a=8, n_b=8)
        if cohens_d is not None
        else None
    )
    perm = (
        PermutationTestResult(observed_difference=1.0, p_value=0.01, num_permutations=100)
        if cohens_d is not None
        else None
    )
    return ReproductionResult(
        spec_id="s",
        claim_id="c",
        label=label,
        control_values=(1.0, 2.0),
        treatment_values=(3.0, 4.0),
        permutation=perm,
        effect_size=effect,
        observed_direction="positive",
        expected_direction="positive",
        validation=ComparisonValidation(errors=(), warnings=()),
        n_control=8,
        n_treatment=8,
    )


class TestQualityLevels:
    def test_inconclusive_is_level_0(self) -> None:
        assert (
            classify_single_result(_tiny_result(ReproductionLabel.INCONCLUSIVE))
            == ReproductionQualityLevel.LEVEL_0_CONCEPTUAL
        )

    def test_not_supported_is_level_1(self) -> None:
        assert (
            classify_single_result(_tiny_result(ReproductionLabel.NOT_SUPPORTED, cohens_d=0.05))
            == ReproductionQualityLevel.LEVEL_1_QUALITATIVE
        )

    def test_contradicted_is_level_1_not_zero(self) -> None:
        assert (
            classify_single_result(_tiny_result(ReproductionLabel.CONTRADICTED, cohens_d=-0.8))
            == ReproductionQualityLevel.LEVEL_1_QUALITATIVE
        )

    def test_supported_is_level_2(self) -> None:
        assert (
            classify_single_result(_tiny_result(ReproductionLabel.SUPPORTED, cohens_d=0.9))
            == ReproductionQualityLevel.LEVEL_2_QUANTITATIVE
        )

    def test_never_auto_assigns_mechanistic_without_evidence(self) -> None:
        level = classify_single_result(_tiny_result(ReproductionLabel.SUPPORTED, cohens_d=0.9))
        assert level != ReproductionQualityLevel.LEVEL_3_MECHANISTIC

    def test_mechanistic_evidence_flag_reaches_level_3(self) -> None:
        level = classify_single_result(
            _tiny_result(ReproductionLabel.SUPPORTED, cohens_d=0.9), mechanistic_evidence=True
        )
        assert level == ReproductionQualityLevel.LEVEL_3_MECHANISTIC

    def test_single_regime_never_reaches_level_4(self) -> None:
        claim, spec, conditions = case_a_plasticity_evolvability_tradeoff(
            population_size=6, generations=3, seeds=(0, 1, 2)
        )
        result = LiteratureReproductionRunner().run(spec, conditions, np.random.default_rng(0))
        level = classify_quality_level_across_regimes({"only_regime": result}, spec)
        assert level != ReproductionQualityLevel.LEVEL_4_ROBUST

    def test_two_weak_regimes_do_not_reach_level_4(self) -> None:
        inconclusive = {
            "a": _tiny_result(ReproductionLabel.INCONCLUSIVE),
            "b": _tiny_result(ReproductionLabel.INCONCLUSIVE),
        }
        _, spec, _ = case_a_plasticity_evolvability_tradeoff(seeds=(0, 1, 2, 3))
        assert (
            classify_quality_level_across_regimes(inconclusive, spec)
            != ReproductionQualityLevel.LEVEL_4_ROBUST
        )


class TestBoundarySweep:
    def test_requires_at_least_two_values(self) -> None:
        with pytest.raises(ValueError, match="at least 2"):
            run_boundary_sweep(
                "period",
                lambda p: case_a_plasticity_evolvability_tradeoff(period=int(p)),
                [10.0],
                np.random.default_rng(0),
            )

    def test_real_sweep_over_case_a_period_produces_one_point_per_value(self) -> None:
        result = run_boundary_sweep(
            "period",
            lambda p: case_a_plasticity_evolvability_tradeoff(
                population_size=6, generations=4, seeds=(0, 1, 2), period=int(p)
            ),
            [5.0, 40.0],
            np.random.default_rng(0),
        )
        assert len(result.points) == 2
        assert result.claim_id == "case_a_plasticity_evolvability_tradeoff"
        assert all(p.result.label in ReproductionLabel for p in result.points)

    def test_transitions_reports_only_differing_consecutive_labels(self) -> None:
        from genevra.literature.boundary_search import BoundarySweepPoint, BoundarySweepResult

        points = (
            BoundarySweepPoint(1.0, _tiny_result(ReproductionLabel.INCONCLUSIVE)),
            BoundarySweepPoint(2.0, _tiny_result(ReproductionLabel.INCONCLUSIVE)),
            BoundarySweepPoint(3.0, _tiny_result(ReproductionLabel.SUPPORTED, cohens_d=0.9)),
        )
        sweep = BoundarySweepResult("period", "case_a", points)
        transitions = sweep.transitions()
        assert len(transitions) == 1
        assert transitions[0] == (2.0, 3.0, "INCONCLUSIVE", "SUPPORTED")


class TestComparisonMatrix:
    def _claim(self) -> LiteratureClaim:
        claim, _spec, _conditions = case_a_plasticity_evolvability_tradeoff()
        return claim

    def test_row_has_all_required_columns(self) -> None:
        claim = self._claim()
        row = ComparisonRow(claim=claim, result=_tiny_result(ReproductionLabel.SUPPORTED, 0.9))
        rendered = row.to_dict()
        assert set(COMPARISON_MATRIX_COLUMNS) <= set(rendered.keys())

    def test_csv_and_markdown_render_without_error(self) -> None:
        claim = self._claim()
        rows = [ComparisonRow(claim=claim, result=_tiny_result(ReproductionLabel.SUPPORTED, 0.9))]
        assert "case_a_plasticity_evolvability_tradeoff" in comparison_matrix_csv(rows)
        assert "case_a_plasticity_evolvability_tradeoff" in comparison_matrix_markdown(rows)

    def test_build_matrix_one_row_per_input(self) -> None:
        claim = self._claim()
        rows = [
            ComparisonRow(claim=claim, result=_tiny_result(ReproductionLabel.SUPPORTED, 0.9)),
            ComparisonRow(claim=claim, result=_tiny_result(ReproductionLabel.INCONCLUSIVE)),
        ]
        assert len(build_comparison_matrix(rows)) == 2


class TestFalsificationRanking:
    def test_mechanism_hypothesis_ranks_first_at_equal_cost(self) -> None:
        hypotheses = generate_falsification_hypotheses("plasticity", "novelty", "positive")
        experiments = generate_falsification_experiments(hypotheses, generation_budget=50)
        ranked = rank_falsification_experiments(hypotheses, experiments)
        assert ranked[0][0].hypothesis_id.endswith("::mechanism")

    def test_rejects_mismatched_lengths(self) -> None:
        hypotheses = generate_falsification_hypotheses("plasticity", "novelty")
        with pytest.raises(ValueError, match="same length"):
            rank_falsification_experiments(hypotheses, [])

    def test_ranking_covers_every_hypothesis(self) -> None:
        hypotheses = generate_falsification_hypotheses("plasticity", "novelty")
        experiments = generate_falsification_experiments(hypotheses)
        ranked = rank_falsification_experiments(hypotheses, experiments)
        assert len(ranked) == len(hypotheses)
