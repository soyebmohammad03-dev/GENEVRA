from __future__ import annotations

import json
from pathlib import Path

import pytest

from genevra.campaign.bundle import generate_campaign_bundle
from genevra.campaign.checkpoint import CampaignCheckpoint, RunStatus
from genevra.campaign.config import AnalysisPlan, CampaignConfig, CampaignMode, default_n_replicates
from genevra.campaign.multiple_comparison import (
    ComparisonRecord,
    build_multiple_comparison_registry,
)
from genevra.campaign.report import CampaignReport
from genevra.campaign.runner import CampaignRunner, condition_values
from genevra.campaign.seeding import derive_condition_seeds, derive_replicate_seeds, derive_run_seed


def _plan() -> AnalysisPlan:
    return AnalysisPlan(
        primary_outcome="metric_x",
        secondary_outcomes=("metric_y",),
        expected_direction="positive",
        comparison="a_vs_b",
        statistical_test="permutation_test",
    )


def _config(**overrides: object) -> CampaignConfig:
    defaults: dict[str, object] = dict(
        campaign_id="test_campaign",
        research_question="does X differ between A and B?",
        hypotheses=("H1: A > B",),
        condition_ids=("a", "b"),
        mode=CampaignMode.PILOT,
        n_replicates=3,
        campaign_seed=42,
        analysis_plan=_plan(),
        population_size=8,
        generations_or_steps=10,
    )
    defaults.update(overrides)
    return CampaignConfig(**defaults)  # type: ignore[arg-type]


class TestSeeding:
    def test_condition_seeds_deterministic(self) -> None:
        assert derive_condition_seeds(1, 3) == derive_condition_seeds(1, 3)

    def test_condition_seeds_independent_across_conditions(self) -> None:
        seeds = derive_condition_seeds(1, 3)
        assert len(set(seeds)) == 3

    def test_different_campaign_seeds_diverge(self) -> None:
        assert derive_condition_seeds(1, 3) != derive_condition_seeds(2, 3)

    def test_replicate_seeds_deterministic_and_distinct(self) -> None:
        r1 = derive_replicate_seeds(7, 5)
        r2 = derive_replicate_seeds(7, 5)
        assert r1 == r2
        assert len(set(r1)) == 5

    def test_derive_run_seed_matches_full_derivation(self) -> None:
        condition_seeds = derive_condition_seeds(99, 4)
        for idx, cseed in enumerate(condition_seeds):
            replicate_seeds = derive_replicate_seeds(cseed, 3)
            for ridx, rseed in enumerate(replicate_seeds):
                assert derive_run_seed(99, idx, ridx) == rseed

    def test_prefix_stability_more_conditions_does_not_change_earlier_ones(self) -> None:
        few = derive_condition_seeds(5, 2)
        many = derive_condition_seeds(5, 5)
        assert few == many[:2]


class TestConfig:
    def test_rejects_duplicate_conditions(self) -> None:
        with pytest.raises(ValueError, match="unique"):
            _config(condition_ids=("a", "a"))

    def test_rejects_empty_conditions(self) -> None:
        with pytest.raises(ValueError, match="non-empty"):
            _config(condition_ids=())

    def test_analysis_plan_rejects_non_seed_replication_unit(self) -> None:
        with pytest.raises(ValueError, match="replication_unit"):
            AnalysisPlan(
                primary_outcome="x",
                secondary_outcomes=(),
                expected_direction="positive",
                comparison="a_vs_b",
                statistical_test="permutation_test",
                replication_unit="organism",
            )

    def test_config_hash_stable(self) -> None:
        c1 = _config()
        c2 = _config()
        assert c1.config_hash() == c2.config_hash()

    def test_config_hash_changes_with_content(self) -> None:
        assert _config().config_hash() != _config(campaign_seed=43).config_hash()

    def test_budget_summary(self) -> None:
        summary = _config().budget_summary()
        assert summary["total_runs"] == 2 * 3
        assert summary["conditions"] == 2

    def test_default_replicates_scale_by_mode(self) -> None:
        assert default_n_replicates(CampaignMode.PILOT) < default_n_replicates(
            CampaignMode.STANDARD
        )
        assert default_n_replicates(CampaignMode.STANDARD) < default_n_replicates(
            CampaignMode.RESEARCH
        )

    def test_analysis_plan_round_trip(self, tmp_path: Path) -> None:
        plan = _plan()
        path = tmp_path / "plan.json"
        plan.save(path)
        assert AnalysisPlan.load(path) == plan


def _run_fn_success(condition_id: str, seed: int, replicate_index: int) -> dict[str, object]:
    return {"condition_id": condition_id, "seed": seed, "metric_x": float(seed % 10)}


def _run_fn_fails_condition_b(
    condition_id: str, seed: int, replicate_index: int
) -> dict[str, object]:
    if condition_id == "b":
        raise RuntimeError("simulated failure")
    return {"condition_id": condition_id, "seed": seed, "metric_x": 1.0}


class TestCheckpointAndRunner:
    def test_fresh_checkpoint_all_pending(self, tmp_path: Path) -> None:
        checkpoint = CampaignCheckpoint.load_or_create(tmp_path / "checkpoint.json")
        assert checkpoint.is_pending("a", 0)

    def test_runner_completes_all_cells(self, tmp_path: Path) -> None:
        config = _config()
        runner = CampaignRunner(config, tmp_path / "runs")
        result = runner.run(_run_fn_success)
        assert set(result.completed_seeds["a"]) | set() == set(result.completed_seeds["a"])
        assert len(result.completed_seeds["a"]) == 3
        assert len(result.completed_seeds["b"]) == 3
        assert not result.failed_seeds["a"]
        assert not result.failed_seeds["b"]

    def test_determinism_same_seed_same_result(self, tmp_path: Path) -> None:
        config = _config()
        r1 = CampaignRunner(config, tmp_path / "run1").run(_run_fn_success)
        r2 = CampaignRunner(config, tmp_path / "run2").run(_run_fn_success)
        assert r1.completed_seeds == r2.completed_seeds
        assert r1.completed["a"] == r2.completed["a"]

    def test_different_campaign_seeds_produce_different_seeds(self, tmp_path: Path) -> None:
        c1 = _config(campaign_seed=1)
        c2 = _config(campaign_seed=2)
        r1 = CampaignRunner(c1, tmp_path / "run1").run(_run_fn_success)
        r2 = CampaignRunner(c2, tmp_path / "run2").run(_run_fn_success)
        assert r1.requested_seeds != r2.requested_seeds

    def test_failure_isolation_condition_a_still_completes(self, tmp_path: Path) -> None:
        config = _config()
        result = CampaignRunner(config, tmp_path / "runs").run(_run_fn_fails_condition_b)
        assert len(result.completed_seeds["a"]) == 3
        assert len(result.failed_seeds["b"]) == 3
        assert not result.completed_seeds["b"]

    def test_resume_does_not_redo_completed_cells(self, tmp_path: Path) -> None:
        config = _config()
        runs_dir = tmp_path / "runs"
        calls: list[tuple[str, int, int]] = []

        def counting_run_fn(
            condition_id: str, seed: int, replicate_index: int
        ) -> dict[str, object]:
            calls.append((condition_id, seed, replicate_index))
            return {"metric_x": float(seed)}

        CampaignRunner(config, runs_dir).run(counting_run_fn)
        n_first_pass = len(calls)
        assert n_first_pass == 6

        # A fresh CampaignRunner against the SAME runs_dir simulates a new
        # process resuming after interruption.
        result = CampaignRunner(config, runs_dir).run(counting_run_fn)
        assert len(calls) == n_first_pass  # no cell was re-executed
        assert len(result.completed_seeds["a"]) == 3
        assert len(result.completed_seeds["b"]) == 3

    def test_resume_after_simulated_interruption(self, tmp_path: Path) -> None:
        """A run left RUNNING (process killed mid-execution) must be
        retried on resume, not treated as completed."""
        config = _config()
        runs_dir = tmp_path / "runs"
        runs_dir.mkdir()
        checkpoint = CampaignCheckpoint.load_or_create(runs_dir / "checkpoint.json")
        checkpoint.mark_running("a", 0, seed=123)
        # Simulate the process dying here (no mark_completed/mark_failed call).

        reloaded = CampaignCheckpoint.load_or_create(runs_dir / "checkpoint.json")
        assert reloaded.runs["a::0"].status is RunStatus.INTERRUPTED
        assert reloaded.is_pending("a", 0)

        result = CampaignRunner(config, runs_dir).run(_run_fn_success)
        assert 0 in [i for i in range(len(result.completed_seeds["a"]))]
        assert len(result.completed_seeds["a"]) == 3

    def test_condition_values_extracts_metric(self, tmp_path: Path) -> None:
        config = _config()
        result = CampaignRunner(config, tmp_path / "runs").run(_run_fn_success)
        values = condition_values(result, "a", "metric_x")
        assert len(values) == 3
        assert all(isinstance(v, float) for v in values.values())

    def test_condition_values_missing_metric_dropped(self, tmp_path: Path) -> None:
        config = _config()

        def sparse_run_fn(condition_id: str, seed: int, replicate_index: int) -> dict[str, object]:
            return {"other_field": 1.0}

        result = CampaignRunner(config, tmp_path / "runs").run(sparse_run_fn)
        values = condition_values(result, "a", "metric_x")
        assert values == {}


class TestMultipleComparison:
    def test_empty_returns_empty(self) -> None:
        assert build_multiple_comparison_registry([]) == []

    def test_labels_primary_as_confirmatory(self) -> None:
        records = [
            ComparisonRecord("h1", "metric_x", "a_vs_b", "permutation_test", 0.01, 0.6, True),
            ComparisonRecord("h2", "metric_y", "a_vs_b", "permutation_test", 0.2, 0.1, False),
        ]
        corrected = build_multiple_comparison_registry(records)
        assert corrected[0].label == "confirmatory"
        assert corrected[1].label == "exploratory"

    def test_does_not_hide_nonsignificant_results(self) -> None:
        records = [
            ComparisonRecord("h1", "m", "a_vs_b", "t", 0.9, 0.0, False),
        ]
        corrected = build_multiple_comparison_registry(records)
        assert len(corrected) == 1
        assert not corrected[0].significant


class TestBundle:
    def test_generates_full_tree(self, tmp_path: Path) -> None:
        config = _config()
        runs_dir = tmp_path / "runs"
        runner = CampaignRunner(config, runs_dir)
        run_result = runner.run(_run_fn_success)
        report = CampaignReport(
            config=config,
            run_result=run_result,
            checkpoint_summary=runner.checkpoint.summary(),
        )
        output_root = tmp_path / "research_artifacts"
        directory = generate_campaign_bundle(
            output_root, config, runner.checkpoint, run_result, report, runs_dir
        )

        base = directory.base
        assert (base / "manifest.json").exists()
        assert (base / "analysis_plan.json").exists()
        assert (base / "quality_gate.json").exists()
        assert (base / "conditions" / "a.json").exists()
        assert (base / "conditions" / "b.json").exists()
        assert (base / "runs" / "checkpoint.json").exists()
        assert (base / "reports" / "report.json").exists()
        assert (base / "reports" / "report.md").exists()
        assert (base / "provenance" / "provenance.json").exists()
        assert base == output_root / "campaigns" / "test_campaign"

    def test_manifest_traces_to_config_hash_and_commit(self, tmp_path: Path) -> None:
        config = _config()
        runs_dir = tmp_path / "runs"
        runner = CampaignRunner(config, runs_dir)
        run_result = runner.run(_run_fn_success)
        report = CampaignReport(
            config=config, run_result=run_result, checkpoint_summary=runner.checkpoint.summary()
        )
        directory = generate_campaign_bundle(
            tmp_path / "research_artifacts", config, runner.checkpoint, run_result, report, runs_dir
        )
        manifest = json.loads((directory.base / "manifest.json").read_text())
        assert manifest["config_hash"] == config.config_hash()
        assert "git_commit" in manifest

    def test_no_orphaned_provenance_seeds_match_completed(self, tmp_path: Path) -> None:
        config = _config()
        runs_dir = tmp_path / "runs"
        runner = CampaignRunner(config, runs_dir)
        run_result = runner.run(_run_fn_success)
        report = CampaignReport(
            config=config, run_result=run_result, checkpoint_summary=runner.checkpoint.summary()
        )
        directory = generate_campaign_bundle(
            tmp_path / "research_artifacts", config, runner.checkpoint, run_result, report, runs_dir
        )
        provenance = json.loads((directory.provenance_dir / "provenance.json").read_text())
        all_completed = {s for seeds in run_result.completed_seeds.values() for s in seeds}
        assert set(provenance["seeds"]) == all_completed
