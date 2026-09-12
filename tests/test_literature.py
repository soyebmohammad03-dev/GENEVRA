"""Phase 11 tests: literature claims/specs, the reproduction runner's
classification core, alternative explanations, falsification generation,
the ResearchMemory-backed registry, report assembly, and the four initial
literature-inspired cases end-to-end on a tiny configuration."""

from __future__ import annotations

import json

import numpy as np
import pytest

from genevra.discovery.memory import ResearchMemory
from genevra.literature.alternative_explanations import (
    STANDARD_CONFOUNDS,
    standard_alternative_explanations,
)
from genevra.literature.cases import (
    case_a_plasticity_evolvability_tradeoff,
    case_b_volatility_and_plasticity,
    case_c_history_dependence,
    case_d_learning_strategy_predicts_potential,
)
from genevra.literature.claims import LiteratureClaim
from genevra.literature.falsification import (
    generate_falsification_experiments,
    generate_falsification_hypotheses,
)
from genevra.literature.registry import config_hash, register_claim, register_reproduction
from genevra.literature.report import build_reproduction_report
from genevra.literature.runner import (
    LiteratureReproductionRunner,
    ReproductionLabel,
    classify_evidence,
    extract_metric,
)
from genevra.literature.spec import LiteratureExperimentSpec

_CASES = [
    case_a_plasticity_evolvability_tradeoff,
    case_b_volatility_and_plasticity,
    case_c_history_dependence,
    case_d_learning_strategy_predicts_potential,
]


def _make_claim(**overrides: object) -> LiteratureClaim:
    defaults = dict(
        claim_id="c1",
        source_reference="Example et al.",
        source_year=2020,
        research_question="q",
        claim_text="text",
        independent_variable="x",
        dependent_variable="y",
        environmental_regime="static",
        organism_assumptions="a",
        evolutionary_assumptions="b",
        measurement_definition="d",
        expected_direction="positive",
        expected_relationship="x increases y",
        known_limitations=("limitation one",),
        genevra_mapping="x -> condition, y -> metric",
    )
    defaults.update(overrides)
    return LiteratureClaim(**defaults)  # type: ignore[arg-type]


def _make_spec(**overrides: object) -> LiteratureExperimentSpec:
    defaults = dict(
        spec_id="s1",
        claim_id="c1",
        control_condition="control",
        treatment_condition="treatment",
        population_size=8,
        generations=5,
        seeds=(0, 1, 2, 3),
        primary_metric="genotypic_diversity",
        statistical_test="permutation_test",
        expected_direction="positive",
    )
    defaults.update(overrides)
    return LiteratureExperimentSpec(**defaults)  # type: ignore[arg-type]


class TestLiteratureClaim:
    def test_round_trip_serialization(self) -> None:
        claim = _make_claim()
        restored = LiteratureClaim.from_dict(json.loads(json.dumps(claim.to_dict())))
        assert restored == claim

    def test_known_limitations_survive_round_trip_as_tuple(self) -> None:
        claim = _make_claim(known_limitations=("a", "b"))
        restored = LiteratureClaim.from_dict(claim.to_dict())
        assert restored.known_limitations == ("a", "b")


class TestLiteratureExperimentSpec:
    def test_round_trip_serialization(self) -> None:
        spec = _make_spec()
        restored = LiteratureExperimentSpec.from_dict(json.loads(json.dumps(spec.to_dict())))
        assert restored == spec

    def test_save_and_load(self, tmp_path: object) -> None:
        import pathlib

        path = pathlib.Path(str(tmp_path)) / "spec.json"
        spec = _make_spec()
        spec.save(path)
        assert LiteratureExperimentSpec.load(path) == spec

    def test_requires_at_least_two_seeds(self) -> None:
        with pytest.raises(ValueError, match="at least 2 seeds"):
            _make_spec(seeds=(0,))

    def test_rejects_duplicate_seeds(self) -> None:
        with pytest.raises(ValueError, match="unique"):
            _make_spec(seeds=(0, 0, 1))

    def test_rejects_invalid_expected_direction(self) -> None:
        with pytest.raises(ValueError, match="expected_direction"):
            _make_spec(expected_direction="sideways")

    def test_rejects_non_positive_population_or_generations(self) -> None:
        with pytest.raises(ValueError, match="population_size"):
            _make_spec(population_size=0)
        with pytest.raises(ValueError, match="generations"):
            _make_spec(generations=0)


class TestExtractMetric:
    def test_simple_key(self) -> None:
        result = {"status": "completed", "trajectory": [{"genotypic_diversity": 1.5}]}
        assert extract_metric(result, "genotypic_diversity") == 1.5

    def test_nested_key(self) -> None:
        result = {"status": "completed", "trajectory": [{"fitness_summary": {"mean": 2.0}}]}
        assert extract_metric(result, "fitness_summary.mean") == 2.0

    def test_sequence_index(self) -> None:
        result = {
            "status": "completed",
            "trajectory": [{"learning_gene_stats": [{"mean": 0.1}, {"mean": 0.2}]}],
        }
        assert extract_metric(result, "learning_gene_stats.1.mean") == 0.2

    def test_out_of_range_index_returns_none(self) -> None:
        result = {"status": "completed", "trajectory": [{"learning_gene_stats": [{"mean": 0.1}]}]}
        assert extract_metric(result, "learning_gene_stats.5.mean") is None

    def test_missing_key_returns_none(self) -> None:
        result = {"status": "completed", "trajectory": [{"other": 1.0}]}
        assert extract_metric(result, "genotypic_diversity") is None

    def test_failed_status_returns_none(self) -> None:
        result = {"status": "failed", "trajectory": [{"genotypic_diversity": 1.0}]}
        assert extract_metric(result, "genotypic_diversity") is None

    def test_empty_trajectory_returns_none(self) -> None:
        result = {"status": "completed", "trajectory": []}
        assert extract_metric(result, "genotypic_diversity") is None

    def test_null_leaf_returns_none(self) -> None:
        result = {"status": "completed", "trajectory": [{"behavior_centroid_shift": None}]}
        assert extract_metric(result, "behavior_centroid_shift") is None


class TestClassifyEvidence:
    def test_requires_at_least_two_values_per_sample(self) -> None:
        rng = np.random.default_rng(0)
        with pytest.raises(ValueError, match="at least 2 values"):
            classify_evidence([1.0], [1.0, 2.0], "positive", 0.90, rng)

    def test_large_clear_positive_effect_is_supported(self) -> None:
        rng = np.random.default_rng(0)
        control = [0.0, 0.05, -0.05, 0.02, -0.02, 0.01]
        treatment = [5.0, 5.1, 4.9, 5.05, 4.95, 5.02]
        label, perm, effect, direction = classify_evidence(
            control, treatment, "positive", 0.90, rng
        )
        assert label == ReproductionLabel.SUPPORTED
        assert direction == "positive"
        assert effect.cohens_d > 0.5
        assert perm.p_value < 0.10

    def test_large_effect_in_opposite_direction_is_contradicted(self) -> None:
        rng = np.random.default_rng(0)
        control = [5.0, 5.1, 4.9, 5.05, 4.95, 5.02]
        treatment = [0.0, 0.05, -0.05, 0.02, -0.02, 0.01]
        label, _perm, _effect, direction = classify_evidence(
            control, treatment, "positive", 0.90, rng
        )
        assert label == ReproductionLabel.CONTRADICTED
        assert direction == "negative"

    def test_indistinguishable_samples_are_inconclusive(self) -> None:
        rng = np.random.default_rng(0)
        control = [0.0, 0.01, -0.01, 0.02, -0.02, 0.0]
        treatment = [0.01, -0.01, 0.0, 0.01, -0.02, 0.02]
        label, *_ = classify_evidence(control, treatment, "positive", 0.90, rng)
        assert label == ReproductionLabel.INCONCLUSIVE


class TestAlternativeExplanations:
    def test_one_explanation_per_standard_confound(self) -> None:
        explanations = standard_alternative_explanations("plasticity", "novelty")
        assert len(explanations) == len(STANDARD_CONFOUNDS)
        assert all(e.status == "untested" for e in explanations)
        assert all(e.evidence == () for e in explanations)

    def test_explanation_ids_are_unique(self) -> None:
        explanations = standard_alternative_explanations("x", "y")
        ids = {e.explanation_id for e in explanations}
        assert len(ids) == len(explanations)


class TestFalsification:
    def test_generates_mechanism_plus_one_per_confound(self) -> None:
        hypotheses = generate_falsification_hypotheses("plasticity", "novelty", "positive")
        assert len(hypotheses) == len(STANDARD_CONFOUNDS) + 1
        assert hypotheses[0].dependent_variable == "novelty"
        assert hypotheses[0].predicted_direction == "positive"

    def test_generated_experiments_are_valid_proposals(self) -> None:
        hypotheses = generate_falsification_hypotheses("plasticity", "novelty")
        proposals = generate_falsification_experiments(
            hypotheses, sample_size=4, generation_budget=10
        )
        assert len(proposals) == len(hypotheses)
        for proposal in proposals:
            assert proposal.validate() == []


class TestRegistry:
    def test_config_hash_is_deterministic(self) -> None:
        spec = _make_spec()
        assert config_hash(spec) == config_hash(spec)

    def test_config_hash_differs_for_different_specs(self) -> None:
        assert config_hash(_make_spec()) != config_hash(_make_spec(spec_id="other"))

    def test_register_claim_is_idempotent(self) -> None:
        memory = ResearchMemory()
        claim = _make_claim()
        first = register_claim(memory, claim)
        second = register_claim(memory, claim)
        assert first == second
        assert len(memory.records) == 1

    def test_register_reproduction_links_to_claim(self) -> None:
        memory = ResearchMemory()
        claim = _make_claim()
        claim_id = register_claim(memory, claim)
        spec = _make_spec()
        rng = np.random.default_rng(0)
        label, perm, effect, direction = classify_evidence(
            [0.0, 0.1, -0.1], [1.0, 1.1, 0.9], "positive", 0.90, rng
        )
        from genevra.analysis.comparison import ComparisonValidation
        from genevra.literature.runner import ReproductionResult

        result = ReproductionResult(
            spec_id=spec.spec_id,
            claim_id=spec.claim_id,
            label=label,
            control_values=(0.0, 0.1, -0.1),
            treatment_values=(1.0, 1.1, 0.9),
            permutation=perm,
            effect_size=effect,
            observed_direction=direction,
            expected_direction=spec.expected_direction,
            validation=ComparisonValidation(errors=(), warnings=()),
            n_control=3,
            n_treatment=3,
        )
        record_id = register_reproduction(memory, spec, result, claim_id, "0.1.0")
        record = memory.get(record_id)
        assert record.parent_ids == (claim_id,)
        assert record.payload["label"] == label.value
        assert memory.children(claim_id) == [record]

    def test_register_reproduction_rejects_duplicate_spec_id(self) -> None:
        memory = ResearchMemory()
        claim_id = register_claim(memory, _make_claim())
        spec = _make_spec()
        rng = np.random.default_rng(0)
        label, perm, effect, direction = classify_evidence(
            [0.0, 0.1], [1.0, 1.1], "positive", 0.90, rng
        )
        from genevra.analysis.comparison import ComparisonValidation
        from genevra.literature.runner import ReproductionResult

        result = ReproductionResult(
            spec_id=spec.spec_id,
            claim_id=spec.claim_id,
            label=label,
            control_values=(0.0, 0.1),
            treatment_values=(1.0, 1.1),
            permutation=perm,
            effect_size=effect,
            observed_direction=direction,
            expected_direction=spec.expected_direction,
            validation=ComparisonValidation(errors=(), warnings=()),
            n_control=2,
            n_treatment=2,
        )
        register_reproduction(memory, spec, result, claim_id, "0.1.0")
        with pytest.raises(ValueError, match="already registered"):
            register_reproduction(memory, spec, result, claim_id, "0.1.0")


class TestReproductionReport:
    def test_to_dict_and_to_text_never_claim_exact_reproduction(self) -> None:
        claim = _make_claim()
        spec = _make_spec()
        conditions_dummy = None  # not needed for this synthetic result
        rng = np.random.default_rng(0)
        label, perm, effect, direction = classify_evidence(
            [0.0, 0.1, -0.1, 0.05], [1.0, 1.1, 0.9, 1.05], "positive", 0.90, rng
        )
        from genevra.analysis.comparison import ComparisonValidation
        from genevra.literature.runner import ReproductionResult

        result = ReproductionResult(
            spec_id=spec.spec_id,
            claim_id=spec.claim_id,
            label=label,
            control_values=(0.0, 0.1, -0.1, 0.05),
            treatment_values=(1.0, 1.1, 0.9, 1.05),
            permutation=perm,
            effect_size=effect,
            observed_direction=direction,
            expected_direction=spec.expected_direction,
            validation=ComparisonValidation(errors=(), warnings=()),
            n_control=4,
            n_treatment=4,
        )
        report = build_reproduction_report(claim, spec, result)
        text = report.to_text()
        assert "original experiment" in text.lower()
        assert "qualitative pattern" in text.lower()
        payload = report.to_dict()
        assert payload["result"]["label"] == label.value
        del conditions_dummy


class TestCasesEndToEnd:
    @pytest.mark.parametrize("case_factory", _CASES)
    def test_case_runs_and_produces_a_valid_label(self, case_factory: object) -> None:
        claim, spec, conditions = case_factory(population_size=6, generations=3, seeds=(0, 1, 2, 3))  # type: ignore[operator]
        assert spec.claim_id == claim.claim_id
        assert spec.control_condition in conditions
        assert spec.treatment_condition in conditions
        result = LiteratureReproductionRunner().run(spec, conditions, np.random.default_rng(0))
        assert result.label in ReproductionLabel
        assert result.n_control >= 2
        assert result.n_treatment >= 2

    def test_every_case_documents_approximations(self) -> None:
        for case_factory in _CASES:
            claim, spec, _conditions = case_factory(population_size=4, generations=2, seeds=(0, 1))  # type: ignore[operator]
            assert claim.known_limitations
            assert spec.approximation_notes
            notes_text = " ".join(spec.approximation_notes).lower()
            assert "approximat" in notes_text or claim.genevra_mapping
