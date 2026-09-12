"""Phase 14.10/14.12: `generate_artifact_bundle` — given a stored
`ExperimentResult` dict (and, optionally, a `ResearchMemory`), writes the
full `research_artifacts/<experiment_id>/` tree: whichever figures the
trajectory data supports, an experiment-summary table, provenance, and a
report. This is also the reproducibility path exercised by
`tests/test_artifacts_integration.py` (Phase 14.12's end-to-end test).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from genevra.artifacts.directory import ArtifactDirectory
from genevra.artifacts.figures import (
    plot_diversity_trajectory,
    plot_fitness_trajectory,
    plot_learning_strategy_trajectory,
    plot_novelty_trajectory,
    plot_overview_panel,
)
from genevra.artifacts.index import build_index
from genevra.artifacts.report import ArtifactReportBundle
from genevra.artifacts.style import FigureMetadata
from genevra.artifacts.tables import (
    EXPERIMENT_SUMMARY_COLUMNS,
    experiment_summary_rows,
    to_csv,
    to_markdown,
)
from genevra.discovery.memory import ResearchMemory


def generate_artifact_bundle(
    result: dict[str, Any],
    output_root: Path,
    research_question: str = "(not specified by caller)",
    memory: ResearchMemory | None = None,
) -> ArtifactReportBundle:
    experiment_id = f"{result.get('name', 'experiment')}_seed{result.get('seed', 0)}"
    directory = ArtifactDirectory(output_root, experiment_id)
    trajectory = result.get("trajectory") or []

    figures: list[FigureMetadata] = []
    if trajectory:
        figures.append(plot_fitness_trajectory(trajectory, directory.figures, experiment_id))
        figures.append(plot_novelty_trajectory(trajectory, directory.figures, experiment_id))
        figures.append(plot_diversity_trajectory(trajectory, directory.figures, experiment_id))
        learning_figure = plot_learning_strategy_trajectory(
            trajectory, directory.figures, experiment_id
        )
        if learning_figure is not None:
            figures.append(learning_figure)
        figures.append(plot_overview_panel(trajectory, directory.figures, experiment_id))

    summary_rows = experiment_summary_rows([result])
    (directory.tables / "experiment_summary.csv").write_text(
        to_csv(summary_rows, EXPERIMENT_SUMMARY_COLUMNS)
    )
    (directory.tables / "experiment_summary.md").write_text(
        to_markdown(summary_rows, EXPERIMENT_SUMMARY_COLUMNS)
    )

    provenance = directory.write_provenance(
        seeds=(result.get("seed", 0),),
        configuration={
            "name": result.get("name"),
            "condition_id": result.get("condition_id"),
            "environment_summary": result.get("environment_summary", {}),
            "software": result.get("software", {}),
        },
    )

    index = build_index(results=[result], memory=memory, figure_count=len(figures), table_count=1)

    status = result.get("status", "unknown")
    main_results_summary = (
        f"Run status: {status}. generations_completed="
        f"{result.get('generations_completed')}, final_population_size="
        f"{result.get('final_population_size')}. See figures/tables for the full "
        "per-generation trajectory; this sentence is a status summary, not a "
        "scientific conclusion."
    )

    bundle = ArtifactReportBundle(
        experiment_id=experiment_id,
        research_question=research_question,
        conditions=(result.get("condition_id") or result.get("name", "unknown"),),
        seeds=provenance.seeds,
        metrics_used=tuple(sorted(trajectory[0].keys())) if trajectory else (),
        statistical_methods=(),
        main_results_summary=main_results_summary,
        figures=tuple(figures),
        table_names=("experiment_summary.csv", "experiment_summary.md"),
        alternative_explanations_summary=(
            "Not evaluated by this single-run bundle; see "
            "genevra.literature.alternative_explanations for the framework used by "
            "literature-reproduction runs."
        ),
        limitations=(
            "A single run/seed; no cross-seed statistical comparison performed here.",
            "Figures reflect only whichever trajectory fields this stored result recorded.",
        ),
        reproduction_status="n/a (not a literature-reproduction experiment)",
        replication_status="n/a (single run; not independently replicated)",
        open_endedness_evidence_summary=(
            "Not evaluated by this bundle; run `genevra open-endedness` separately."
        ),
        index=index,
    )
    (directory.reports / "report.json").write_text(json.dumps(bundle.to_dict(), indent=2))
    (directory.reports / "report.md").write_text(bundle.to_text())
    return bundle


__all__ = ["generate_artifact_bundle"]
