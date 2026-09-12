"""Phase 14.12: run experiment -> save result -> generate figures ->
generate tables -> generate report -> verify provenance links everything
together. This is GENEVRA's core research-artifact-reproducibility test.
"""

from __future__ import annotations

import json

import pytest

matplotlib = pytest.importorskip("matplotlib")
matplotlib.use("Agg")

from genevra.artifacts.bundle import generate_artifact_bundle  # noqa: E402
from genevra.experiments.runner import ExperimentRunner  # noqa: E402
from tests.factories import make_config_factory  # noqa: E402


def test_full_artifact_bundle_reproducibility(tmp_path) -> None:
    config = make_config_factory(max_steps=15)(seed=42)
    result = ExperimentRunner(config, condition_id="baseline").run()
    assert result.status == "completed"

    result_dict = result.to_dict()
    result_path = tmp_path / "result.json"
    result_path.write_text(json.dumps(result_dict, indent=2))

    reloaded = json.loads(result_path.read_text())
    bundle = generate_artifact_bundle(
        reloaded, tmp_path / "research_artifacts", research_question="Does X happen under Y?"
    )

    experiment_dir = tmp_path / "research_artifacts" / bundle.experiment_id
    assert experiment_dir.is_dir()

    figure_dir = experiment_dir / "figures"
    assert (figure_dir / "fitness_trajectory.png").exists()
    assert (figure_dir / "overview_panel.png").exists()
    for figure in bundle.figures:
        for filename in figure.files:
            assert (figure_dir / filename).exists()
        sidecar = json.loads((figure_dir / f"{figure.figure_id}.json").read_text())
        assert sidecar["experiment_id"] == bundle.experiment_id

    table_dir = experiment_dir / "tables"
    assert (table_dir / "experiment_summary.csv").exists()
    assert (table_dir / "experiment_summary.md").exists()

    provenance = json.loads((experiment_dir / "provenance" / "provenance.json").read_text())
    assert provenance["experiment_id"] == bundle.experiment_id
    assert provenance["seeds"] == [42]

    seeds_on_disk = json.loads((experiment_dir / "seeds" / "seeds.json").read_text())
    assert seeds_on_disk == [42]

    report_json = json.loads((experiment_dir / "reports" / "report.json").read_text())
    assert report_json["experiment_id"] == bundle.experiment_id
    assert report_json["seeds"] == [42]
    report_md = (experiment_dir / "reports" / "report.md").read_text()
    assert "Scientific-Language Safeguards" in report_md
    assert bundle.experiment_id in report_md

    # provenance consistency: every figure's experiment_id matches the
    # directory's provenance experiment_id and seed set.
    assert bundle.index.experiment_count == 1
    assert bundle.index.seed_count == 1


def test_artifact_bundle_handles_failed_run(tmp_path) -> None:
    """A failed run must still produce a bundle (no figures, since there
    is no trajectory) — Phase 14's "do not hide failed runs" requirement."""
    result = {
        "name": "broken",
        "seed": 1,
        "status": "failed",
        "trajectory": [],
        "lineage": [],
        "final_population_size": 0,
        "generations_completed": 0,
        "environment_summary": {},
        "condition_id": None,
        "failure": {"type": "ValueError", "message": "boom"},
        "software": {},
    }
    bundle = generate_artifact_bundle(result, tmp_path / "research_artifacts")
    assert bundle.figures == ()
    assert "failed" in bundle.main_results_summary
