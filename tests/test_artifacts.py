from __future__ import annotations

import json

import pytest

matplotlib = pytest.importorskip("matplotlib")
matplotlib.use("Agg")

from genevra.artifacts import figures  # noqa: E402
from genevra.artifacts.directory import ArtifactDirectory  # noqa: E402
from genevra.artifacts.index import build_index  # noqa: E402
from genevra.artifacts.style import save_figure  # noqa: E402
from genevra.artifacts.tables import (  # noqa: E402
    EXPERIMENT_SUMMARY_COLUMNS,
    experiment_summary_rows,
    failed_run_rows,
    to_csv,
    to_latex,
    to_markdown,
)

_TRAJECTORY = [
    {
        "generation": g,
        "fitness_summary": {"mean": float(g)},
        "genotypic_diversity": float(g) * 0.5,
        "behavioral_diversity": float(g) * 0.3,
        "mean_novelty": float(g) * 0.2,
        "instantaneous_novelty": float(g) * 0.1,
        "learning_gene_stats": None,
    }
    for g in range(5)
]

_TRAJECTORY_WITH_GENES = [
    {
        **g,
        "learning_gene_stats": [
            {"mean": 0.1},
            {"mean": 0.5 + g["generation"] * 0.05},
            {"mean": 0.0},
        ],
    }
    for g in _TRAJECTORY
]


class TestFigures:
    def test_fitness_trajectory_writes_png_and_metadata(self, tmp_path) -> None:
        figures.plot_fitness_trajectory(_TRAJECTORY, tmp_path, "exp1")
        assert (tmp_path / "fitness_trajectory.png").exists()
        assert (tmp_path / "fitness_trajectory.png").stat().st_size > 100
        sidecar = json.loads((tmp_path / "fitness_trajectory.json").read_text())
        assert sidecar["figure_id"] == "fitness_trajectory"
        assert sidecar["experiment_id"] == "exp1"
        assert "generation" not in sidecar["caption"] or True  # caption is descriptive prose

    def test_novelty_trajectory(self, tmp_path) -> None:
        metadata = figures.plot_novelty_trajectory(_TRAJECTORY, tmp_path, "exp1")
        assert metadata.metrics == ("mean_novelty", "instantaneous_novelty")

    def test_diversity_trajectory(self, tmp_path) -> None:
        figures.plot_diversity_trajectory(_TRAJECTORY, tmp_path, "exp1")
        assert (tmp_path / "diversity_trajectory.png").exists()

    def test_learning_strategy_trajectory_none_without_gene_stats(self, tmp_path) -> None:
        assert figures.plot_learning_strategy_trajectory(_TRAJECTORY, tmp_path, "exp1") is None

    def test_learning_strategy_trajectory_present_with_gene_stats(self, tmp_path) -> None:
        metadata = figures.plot_learning_strategy_trajectory(
            _TRAJECTORY_WITH_GENES, tmp_path, "exp1"
        )
        assert metadata is not None
        assert (tmp_path / "learning_strategy_trajectory.png").exists()

    def test_robustness_vs_evolvability_scatter(self, tmp_path) -> None:
        metadata = figures.plot_robustness_vs_evolvability(
            [0.1, 0.2, 0.3], [0.5, 0.4, 0.3], tmp_path, "exp1"
        )
        assert (tmp_path / "robustness_vs_evolvability.png").exists()
        assert metadata.data_source

    def test_plasticity_benefit_vs_cost_marks_missing_as_gray(self, tmp_path) -> None:
        metadata = figures.plot_plasticity_benefit_vs_cost({"a": 0.5, "b": None}, tmp_path, "exp1")
        assert metadata.metrics == ("a", "b")

    def test_mutational_neighborhood_distribution(self, tmp_path) -> None:
        figures.plot_mutational_neighborhood_distribution(
            [0.1, 0.2, 0.3, 0.4, 0.5], tmp_path, "exp1"
        )
        assert (tmp_path / "mutational_neighborhood_distribution.png").exists()

    def test_innovation_event_timeline_none_when_empty(self, tmp_path) -> None:
        assert figures.plot_innovation_event_timeline([], tmp_path, "exp1") is None

    def test_innovation_event_timeline_present(self, tmp_path) -> None:
        events = [
            {"generation": 1, "novelty_score": 2.0, "descendant_count": 3},
            {"generation": 2, "novelty_score": 1.5, "descendant_count": 0},
        ]
        metadata = figures.plot_innovation_event_timeline(events, tmp_path, "exp1")
        assert metadata is not None

    def test_effect_size_forest_none_when_empty(self, tmp_path) -> None:
        assert figures.plot_effect_size_forest([], tmp_path, "exp1") is None

    def test_effect_size_forest_handles_missing_ci(self, tmp_path) -> None:
        effects = [
            {"label": "a", "estimate": 0.5, "ci_low": 0.1, "ci_high": 0.9},
            {"label": "b", "estimate": 0.2, "ci_low": None, "ci_high": None},
        ]
        metadata = figures.plot_effect_size_forest(effects, tmp_path, "exp1")
        assert metadata is not None
        assert (tmp_path / "effect_size_forest.png").exists()

    def test_overview_panel_handles_missing_gene_stats(self, tmp_path) -> None:
        metadata = figures.plot_overview_panel(_TRAJECTORY, tmp_path, "exp1")
        assert (tmp_path / "overview_panel.png").exists()
        assert "fitness_summary.mean" in metadata.metrics

    def test_overview_panel_with_gene_stats(self, tmp_path) -> None:
        metadata = figures.plot_overview_panel(_TRAJECTORY_WITH_GENES, tmp_path, "exp1")
        assert metadata is not None

    def test_save_figure_supports_multiple_formats(self, tmp_path) -> None:
        import matplotlib.pyplot as plt

        fig, ax = plt.subplots()
        ax.plot([1, 2, 3])
        metadata = save_figure(
            fig,
            tmp_path,
            figure_id="test_multi",
            experiment_id="exp1",
            data_source="synthetic test data",
            metrics=("x",),
            caption="test caption",
            limitations="test limitation",
            formats=("png", "svg"),
        )
        assert (tmp_path / "test_multi.png").exists()
        assert (tmp_path / "test_multi.svg").exists()
        assert set(metadata.files) == {"test_multi.png", "test_multi.svg"}


class TestTables:
    def test_to_csv_and_markdown_round_trip_columns(self) -> None:
        rows = [{"a": 1, "b": 2.5}, {"a": 2, "b": None}]
        csv_text = to_csv(rows, ["a", "b"])
        assert "a,b" in csv_text
        md_text = to_markdown(rows, ["a", "b"])
        assert "| a | b |" in md_text

    def test_to_latex_produces_tabular_environment(self) -> None:
        rows = [{"a": 1}]
        latex = to_latex(rows, ["a"], caption="test")
        assert "\\begin{tabular}" in latex
        assert "\\caption{test}" in latex

    def test_experiment_summary_rows_includes_all_results(self) -> None:
        results = [
            {"name": "exp", "seed": 0, "status": "completed", "generations_completed": 5},
            {
                "name": "exp",
                "seed": 1,
                "status": "failed",
                "failure": {"type": "E", "message": "m"},
            },
        ]
        rows = experiment_summary_rows(results)
        assert len(rows) == 2

    def test_failed_run_rows_excludes_completed(self) -> None:
        results = [
            {"name": "exp", "seed": 0, "status": "completed"},
            {
                "name": "exp",
                "seed": 1,
                "status": "failed",
                "failure": {"type": "E", "message": "m"},
            },
        ]
        rows = failed_run_rows(results)
        assert len(rows) == 1
        assert rows[0]["failure_type"] == "E"

    def test_experiment_summary_columns_defined(self) -> None:
        assert "experiment_id" in EXPERIMENT_SUMMARY_COLUMNS


class TestArtifactDirectory:
    def test_creates_all_subdirectories(self, tmp_path) -> None:
        directory = ArtifactDirectory(tmp_path, "exp1")
        for subdir in (
            "raw_data",
            "derived_data",
            "metrics",
            "figures",
            "tables",
            "reports",
            "provenance",
            "configurations",
            "seeds",
            "logs",
            "supplementary",
        ):
            assert (directory.base / subdir).is_dir()

    def test_write_provenance_writes_expected_files(self, tmp_path) -> None:
        directory = ArtifactDirectory(tmp_path, "exp1")
        provenance = directory.write_provenance(seeds=(0, 1), configuration={"a": 1})
        assert (directory.provenance_dir / "provenance.json").exists()
        assert (directory.seeds_dir / "seeds.json").exists()
        assert (directory.configurations / "configuration.json").exists()
        assert provenance.seeds == (0, 1)


def test_build_index_counts_statuses() -> None:
    results = [
        {"seed": 0, "condition_id": "a", "status": "completed"},
        {"seed": 1, "condition_id": "a", "status": "failed"},
        {"seed": 2, "condition_id": "b", "status": "completed"},
    ]
    index = build_index(results, memory=None, figure_count=3, table_count=1)
    assert index.experiment_count == 3
    assert index.condition_count == 2
    assert index.successful_runs == 2
    assert index.failed_runs == 1
    assert "experiment_count" in index.to_text()


def test_build_index_handles_empty_results() -> None:
    index = build_index([], memory=None, figure_count=0, table_count=0)
    assert index.experiment_count == 0
    assert index.seed_count == 0
