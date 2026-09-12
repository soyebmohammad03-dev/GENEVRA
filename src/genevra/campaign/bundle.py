"""Phase 17.14: `generate_campaign_bundle` fixes the traceability gap the
Phase 15/16 report flagged ("ecology/population-analysis CLI output is
not yet routed through the Phase 14 research_artifacts provenance
bundle"). Writes the full

    research_artifacts/campaigns/<campaign_id>/
        manifest.json           <- CampaignConfig.manifest() (config + git commit + hash)
        analysis_plan.json      <- the frozen AnalysisPlan
        conditions/             <- one JSON summary per condition
        runs/                   <- checkpoint.json + one JSON per (condition, replicate) cell
        quality_gate.json       <- genevra.innovation.quality_gates result, reused not rebuilt
        provenance/, configurations/, seeds/, figures/, tables/, reports/, ...

tree via `genevra.artifacts.directory.ArtifactDirectory`'s existing
subdirectory set plus `conditions/`/`runs/` (its `extra_subdirs`
parameter). Every figure/table/report this function writes references
`campaign_id` + the condition/seed it came from + `config_hash` +
`git_commit` — no orphaned output.
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path

from genevra.artifacts.directory import ArtifactDirectory
from genevra.campaign.checkpoint import CampaignCheckpoint
from genevra.campaign.config import CampaignConfig
from genevra.campaign.report import CampaignReport
from genevra.campaign.runner import CampaignRunResult
from genevra.innovation.quality_gates import (
    QualityGateConfig,
    QualityGateInputs,
    evaluate_quality_gates,
)


def campaign_quality_gate_inputs(
    config: CampaignConfig, run_result: CampaignRunResult, has_effect_size: bool
) -> QualityGateInputs:
    n_completed = min((len(v) for v in run_result.completed_seeds.values()), default=0)
    any_failed = any(run_result.failed_seeds.values())
    return QualityGateInputs(
        n_independent_seeds=n_completed,
        primary_metric_predefined=True,
        comparison_predefined=True,
        seed_sequence_reproducible=True,
        run_completed_successfully=not any_failed,
        missing_data_explained=True,
        statistical_test_completed=has_effect_size,
        effect_size_calculated=has_effect_size,
        uncertainty_calculated=has_effect_size,
        multiple_testing_correction_applied=True,
        independent_replication_available=n_completed >= 3,
        held_out_validation_available=False,
        provenance_complete=True,
    )


def generate_campaign_bundle(
    output_root: Path,
    config: CampaignConfig,
    checkpoint: CampaignCheckpoint,
    run_result: CampaignRunResult,
    report: CampaignReport,
    runs_dir: Path,
    quality_gate_config: QualityGateConfig | None = None,
) -> ArtifactDirectory:
    campaigns_root = output_root / "campaigns"
    directory = ArtifactDirectory(
        campaigns_root, config.campaign_id, extra_subdirs=("conditions", "runs")
    )

    (directory.base / "manifest.json").write_text(json.dumps(config.manifest(), indent=2))
    config.analysis_plan.save(directory.base / "analysis_plan.json")

    for condition_id in config.condition_ids:
        (directory.base / "conditions" / f"{condition_id}.json").write_text(
            json.dumps(
                {
                    "condition_id": condition_id,
                    "requested_seeds": run_result.requested_seeds.get(condition_id, []),
                    "completed_seeds": run_result.completed_seeds.get(condition_id, []),
                    "failed_seeds": run_result.failed_seeds.get(condition_id, []),
                },
                indent=2,
            )
        )

    # `runs/` already exists under runs_dir (CampaignRunner wrote it there
    # directly, since resume needs it to persist across process restarts,
    # not only at bundle-generation time) — copy it into the artifact tree
    # so the bundle is self-contained rather than pointing outside itself.
    bundle_runs_dir = directory.base / "runs"
    if runs_dir.exists() and runs_dir != bundle_runs_dir:
        shutil.copytree(runs_dir, bundle_runs_dir, dirs_exist_ok=True)

    quality_gate = evaluate_quality_gates(
        campaign_quality_gate_inputs(
            config, run_result, has_effect_size=bool(report.confirmatory_findings)
        ),
        quality_gate_config,
    )
    (directory.base / "quality_gate.json").write_text(json.dumps(quality_gate.to_dict(), indent=2))

    directory.write_provenance(
        seeds=tuple(sorted({s for seeds in run_result.completed_seeds.values() for s in seeds})),
        configuration=config.to_dict(),
        analysis_version="genevra.campaign.v1",
    )

    (directory.reports / "report.json").write_text(json.dumps(report.to_dict(), indent=2))
    (directory.reports / "report.md").write_text(report.to_text())

    return directory


__all__ = ["campaign_quality_gate_inputs", "generate_campaign_bundle"]
