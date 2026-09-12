"""Phase 12 tests: innovation event detection, dependency graphs,
evolutionary activity, potential-vs-realized, trajectory shape
classification, phase-space projection, quality gates, and the
OpenEndednessAnalyzer/report assembled from them — including finite-run
and empty/zero edge cases."""

from __future__ import annotations

import numpy as np
import pytest

from genevra.evolution.lineage import LineageEvent, LineageTracker
from genevra.innovation.activity import build_activity_report
from genevra.innovation.analyzer import OpenEndednessAnalyzer, OpenEndednessAnalyzerConfig
from genevra.innovation.dependency_graph import build_innovation_dependency_graph
from genevra.innovation.events import InnovationEvent, detect_innovation_events
from genevra.innovation.phase_space import build_phase_space_trajectory, project_phase_space
from genevra.innovation.potential_vs_realized import build_potential_vs_realized_report
from genevra.innovation.quality_gates import (
    QualityGateConfig,
    QualityGateInputs,
    evaluate_quality_gates,
)
from genevra.innovation.report import build_open_endedness_lab_report
from genevra.innovation.trajectory import build_trajectory_report, classify_metric_trajectory


def _make_tracker(events: list[LineageEvent]) -> LineageTracker:
    tracker = LineageTracker()
    for event in events:
        tracker._events[event.individual_id] = event  # test-only direct construction
    return tracker


def _event(
    individual_id: int,
    parent_ids: tuple[int, ...],
    generation: int,
    strategy: tuple[float, float, float] = (0.1, 1.0, 0.0),
    death_generation: int | None = None,
    reproduced: bool = False,
) -> LineageEvent:
    return LineageEvent(
        individual_id=individual_id,
        parent_ids=parent_ids,
        generation=generation,
        genome_hash=f"hash{individual_id}",
        death_generation=death_generation,
        reproduced=reproduced,
        learning_strategy=strategy,
    )


class TestInnovationEventDetection:
    def test_no_events_below_min_cohort_size(self) -> None:
        events = [_event(0, (), 0), _event(1, (), 0)]
        tracker = _make_tracker(events)
        assert detect_innovation_events(events, tracker, min_cohort_size=3) == []

    def test_no_events_when_cohort_has_zero_variance(self) -> None:
        events = [_event(i, (), 0, strategy=(0.1, 1.0, 0.0)) for i in range(5)]
        tracker = _make_tracker(events)
        assert detect_innovation_events(events, tracker) == []

    def test_flags_a_clear_outlier(self) -> None:
        events = [_event(i, (), 0, strategy=(0.1, 1.0, 0.0)) for i in range(5)]
        events.append(_event(5, (), 0, strategy=(10.0, 1.0, 0.0)))
        tracker = _make_tracker(events)
        detected = detect_innovation_events(events, tracker, z_threshold=2.0)
        assert len(detected) == 1
        assert detected[0].lineage == 5
        assert detected[0].fitness_effect is None
        assert detected[0].complexity_score is None

    def test_descendant_count(self) -> None:
        events = [
            _event(i, (), 0, strategy=(0.1, 1.0, 0.0)) for i in range(5)
        ] + [_event(5, (), 0, strategy=(10.0, 1.0, 0.0))]
        events.append(_event(6, (5,), 1))
        events.append(_event(7, (6,), 2))
        tracker = _make_tracker(events)
        detected = detect_innovation_events(events, tracker, z_threshold=2.0)
        assert detected[0].descendant_count == 2

    def test_persistence_duration_none_when_still_alive(self) -> None:
        events = [_event(i, (), 0, strategy=(0.1, 1.0, 0.0)) for i in range(5)]
        events.append(_event(5, (), 0, strategy=(10.0, 1.0, 0.0), death_generation=None))
        tracker = _make_tracker(events)
        detected = detect_innovation_events(events, tracker)
        assert detected[0].persistence_duration is None

    def test_rejects_invalid_thresholds(self) -> None:
        with pytest.raises(ValueError, match="z_threshold"):
            detect_innovation_events([], LineageTracker(), z_threshold=0.0)
        with pytest.raises(ValueError, match="min_cohort_size"):
            detect_innovation_events([], LineageTracker(), min_cohort_size=1)

    def test_empty_lineage_events_produce_no_innovations(self) -> None:
        assert detect_innovation_events([], LineageTracker()) == []


class TestDependencyGraph:
    def test_no_edges_between_unrelated_lineages(self) -> None:
        e1 = InnovationEvent(
            event_id="a", generation=0, lineage=0, behavior_descriptor=(0.0, 0.0, 0.0),
            novelty_score=3.0,
        )
        e2 = InnovationEvent(
            event_id="b", generation=1, lineage=1, behavior_descriptor=(0.0, 0.0, 0.0),
            novelty_score=3.0,
        )
        tracker = _make_tracker([_event(0, (), 0), _event(1, (), 0)])
        graph = build_innovation_dependency_graph([e1, e2], tracker)
        assert graph.edges == ()

    def test_edge_only_for_actual_descent(self) -> None:
        events = [_event(0, (), 0), _event(1, (0,), 1), _event(2, (), 0)]
        tracker = _make_tracker(events)
        e1 = InnovationEvent(
            event_id="a", generation=0, lineage=0, behavior_descriptor=(0.0, 0.0, 0.0),
            novelty_score=3.0,
        )
        e2 = InnovationEvent(
            event_id="b", generation=1, lineage=1, behavior_descriptor=(0.0, 0.0, 0.0),
            novelty_score=3.0,
        )
        e3 = InnovationEvent(
            event_id="c", generation=1, lineage=2, behavior_descriptor=(0.0, 0.0, 0.0),
            novelty_score=3.0,
        )
        graph = build_innovation_dependency_graph([e1, e2, e3], tracker)
        assert graph.descendants_of("a") == ["b"]
        assert graph.ancestors_of("b") == ["a"]
        assert graph.descendants_of("c") == []

    def test_empty_events_produce_empty_graph(self) -> None:
        graph = build_innovation_dependency_graph([], LineageTracker())
        assert graph.events == ()
        assert graph.edges == ()


class TestActivity:
    def test_requires_non_empty_trajectory(self) -> None:
        with pytest.raises(ValueError, match="non-empty"):
            build_activity_report([], [], np.random.default_rng(0))

    def test_full_lineage_persistence_when_all_founders_survive(self) -> None:
        trajectory = [
            {"generation": 0, "behavioral_diversity": 0.1},
            {"generation": 1, "behavioral_diversity": 0.2},
        ]
        events = [
            _event(0, (), 0, death_generation=None),
            _event(1, (0,), 1, death_generation=None),
        ]
        report = build_activity_report(trajectory, events, np.random.default_rng(0))
        assert report.lineage_persistence == 1.0
        assert report.n_generations_observed == 2

    def test_zero_lineage_persistence_when_founder_line_died_out(self) -> None:
        trajectory = [{"generation": 0, "behavioral_diversity": 0.1}]
        events = [_event(0, (), 0, death_generation=0)]
        report = build_activity_report(trajectory, events, np.random.default_rng(0))
        assert report.lineage_persistence == 0.0

    def test_no_lineage_events_gives_empty_strategy_data(self) -> None:
        trajectory = [{"generation": 0, "behavioral_diversity": 0.1}]
        report = build_activity_report(trajectory, [], np.random.default_rng(0))
        assert report.strategy_summaries == ()
        assert report.strategy_turnover_series == ()


class TestPotentialVsRealized:
    def test_empty_samples_yield_zero_report(self) -> None:
        report = build_potential_vs_realized_report([], {})
        assert report.samples == ()
        assert report.realized_minus_potential_mean == 0.0
        assert report.sign_agreement_fraction is None

    def test_single_sample_has_no_sign_agreement(self) -> None:
        from genevra.analysis.evolvability_over_time import EvolvabilitySample
        from genevra.metrics.evolvability import EvolvabilityReport

        samples = [
            EvolvabilitySample(
                generation=0,
                individual_id=0,
                report=EvolvabilityReport(
                    num_samples=5, num_viable=5, mean_behavioral_distance=0.5,
                    behavioral_distance_std=0.0, viable_fraction=1.0,
                ),
            )
        ]
        report = build_potential_vs_realized_report(samples, {0: 0.3})
        assert len(report.samples) == 1
        assert report.sign_agreement_fraction is None


class TestTrajectoryShapes:
    def test_short_series_is_plateau(self) -> None:
        summary = classify_metric_trajectory([1.0], "m", np.random.default_rng(0))
        assert summary.shape == "plateau"

    def test_constant_series_is_plateau(self) -> None:
        summary = classify_metric_trajectory([1.0] * 10, "m", np.random.default_rng(0))
        assert summary.shape == "plateau"

    def test_clear_increase_is_sustained_increase(self) -> None:
        values = list(np.linspace(0, 10, 20))
        summary = classify_metric_trajectory(values, "m", np.random.default_rng(0))
        assert summary.shape in ("sustained_increase", "regime_shift")

    def test_build_trajectory_report_covers_all_metrics(self) -> None:
        report = build_trajectory_report(
            {"a": [1.0, 2.0, 3.0], "b": [3.0, 2.0, 1.0]}, np.random.default_rng(0)
        )
        assert {s.metric_name for s in report.metric_summaries} == {"a", "b"}


class TestPhaseSpace:
    def test_mismatched_lengths_raise(self) -> None:
        with pytest.raises(ValueError, match="expected"):
            build_phase_space_trajectory({"a": [1.0, 2.0]}, [0, 1, 2])

    def test_no_dimensions_raises(self) -> None:
        with pytest.raises(ValueError, match="at least one dimension"):
            build_phase_space_trajectory({}, [0, 1])

    def test_projection_explained_variance_sums_leq_one(self) -> None:
        traj = build_phase_space_trajectory({"a": [1.0, 2.0, 3.0], "b": [1.0, 1.5, 3.0]}, [0, 1, 2])
        projection = project_phase_space(traj, n_components=2)
        assert sum(projection.explained_variance_ratio) <= 1.0 + 1e-9

    def test_zero_variance_dimension_does_not_crash(self) -> None:
        traj = build_phase_space_trajectory({"a": [1.0, 1.0, 1.0]}, [0, 1, 2])
        projection = project_phase_space(traj, n_components=1)
        assert projection.explained_variance_ratio == (0.0,)


class TestQualityGates:
    def _passing_inputs(self) -> QualityGateInputs:
        return QualityGateInputs(
            n_independent_seeds=5,
            primary_metric_predefined=True,
            comparison_predefined=True,
            seed_sequence_reproducible=True,
            run_completed_successfully=True,
            missing_data_explained=True,
            statistical_test_completed=True,
            effect_size_calculated=True,
            uncertainty_calculated=True,
            multiple_testing_correction_applied=False,
            independent_replication_available=False,
            held_out_validation_available=False,
            provenance_complete=True,
        )

    def test_all_default_gates_pass(self) -> None:
        result = evaluate_quality_gates(self._passing_inputs())
        assert result.research_ready is True
        assert "multiple-testing correction applied" in result.exempted_gates

    def test_insufficient_seeds_fails_gate(self) -> None:
        inputs = self._passing_inputs()
        inputs = QualityGateInputs(**{**inputs.__dict__, "n_independent_seeds": 1})
        result = evaluate_quality_gates(inputs)
        assert result.research_ready is False
        assert "sufficient independent seeds" in result.failed_gates

    def test_gate_can_be_disabled(self) -> None:
        inputs = self._passing_inputs()
        inputs = QualityGateInputs(**{**inputs.__dict__, "n_independent_seeds": 1})
        config = QualityGateConfig(require_min_seeds=False)
        result = evaluate_quality_gates(inputs, config)
        assert "sufficient independent seeds" in result.exempted_gates
        assert result.research_ready is True


class TestOpenEndednessAnalyzerIntegration:
    def test_analyze_on_minimal_trajectory_and_lineage(self) -> None:
        trajectory = [
            {
                "generation": g,
                "instantaneous_novelty": 0.1 * g,
                "genotypic_diversity": 0.2 * g,
                "behavioral_diversity": 0.15 * g,
                "fitness_summary": {"mean": 1.0 + 0.01 * g},
            }
            for g in range(6)
        ]
        events = [_event(i, (), 0, strategy=(0.1, 1.0, 0.0)) for i in range(5)]
        events.append(_event(5, (), 0, strategy=(10.0, 1.0, 0.0)))
        tracker = _make_tracker(events)
        rng = np.random.default_rng(0)
        report = OpenEndednessAnalyzer().analyze(trajectory, events, tracker, rng)
        assert report.base is not None
        assert report.innovation_events is not None
        assert report.activity is not None
        assert report.trajectory is not None

        graph = build_innovation_dependency_graph(report.innovation_events, tracker)
        lab_report = build_open_endedness_lab_report(report, dependency_graph=graph)
        text = lab_report.to_text()
        assert "NOT declared 'fully open-ended'" in text
        payload = lab_report.to_dict()
        assert payload["analysis"]["base"] is not None

    def test_disabled_measurements_are_none(self) -> None:
        trajectory = [
            {
                "generation": 0,
                "instantaneous_novelty": 0.1,
                "genotypic_diversity": 0.1,
                "behavioral_diversity": 0.1,
                "fitness_summary": {"mean": 1.0},
            }
        ]
        config = OpenEndednessAnalyzerConfig(
            enable_innovation_events=False, enable_activity=False, enable_trajectory=False
        )
        report = OpenEndednessAnalyzer(config).analyze(
            trajectory, [], LineageTracker(), np.random.default_rng(0)
        )
        assert report.innovation_events is None
        assert report.activity is None
        assert report.trajectory is None

    def test_empty_trajectory_does_not_crash_activity_or_trajectory(self) -> None:
        report = OpenEndednessAnalyzer().analyze([], [], LineageTracker(), np.random.default_rng(0))
        assert report.activity is None
        assert report.trajectory is None
