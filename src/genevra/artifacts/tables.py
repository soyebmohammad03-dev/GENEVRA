"""Phase 14.4: scientific tables, exported to CSV, Markdown, and a
minimal LaTeX `tabular` environment. Every table is built from a plain
list of row dicts — no table function computes a statistic itself, it
only formats numbers a caller already computed (comparison/effect-size/
replication/quality-gate results).
"""

from __future__ import annotations

import csv
import io
from collections.abc import Mapping, Sequence
from typing import Any


def _fmt(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, float):
        return f"{value:.4g}"
    return str(value)


def to_csv(rows: Sequence[Mapping[str, Any]], columns: Sequence[str]) -> str:
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(columns)
    for row in rows:
        writer.writerow([_fmt(row.get(c)) for c in columns])
    return buffer.getvalue()


def to_markdown(rows: Sequence[Mapping[str, Any]], columns: Sequence[str]) -> str:
    lines = ["| " + " | ".join(columns) + " |", "|" + "|".join("---" for _ in columns) + "|"]
    for row in rows:
        lines.append("| " + " | ".join(_fmt(row.get(c)) for c in columns) + " |")
    return "\n".join(lines)


def to_latex(rows: Sequence[Mapping[str, Any]], columns: Sequence[str], caption: str = "") -> str:
    """A minimal `tabular` environment — no external LaTeX dependency,
    just string formatting (Phase 14.4's "if practical" LaTeX support,
    kept as small as the CSV/Markdown exporters)."""
    lines = [
        "\\begin{table}[h]",
        "\\centering",
        "\\begin{tabular}{" + "l" * len(columns) + "}",
        "\\hline",
        " & ".join(columns) + " \\\\",
        "\\hline",
    ]
    for row in rows:
        lines.append(" & ".join(_fmt(row.get(c)) for c in columns) + " \\\\")
    lines.append("\\hline")
    lines.append("\\end{tabular}")
    if caption:
        lines.append(f"\\caption{{{caption}}}")
    lines.append("\\end{table}")
    return "\n".join(lines)


EXPERIMENT_SUMMARY_COLUMNS = (
    "experiment_id",
    "condition_id",
    "seed",
    "status",
    "generations_completed",
    "final_population_size",
)

CONDITION_SUMMARY_COLUMNS = (
    "condition_id",
    "n_seeds",
    "primary_metric",
    "effect_size",
    "ci_low",
    "ci_high",
    "p_value",
    "corrected_p_value",
    "replication_status",
    "quality_gate_status",
)

FAILED_RUN_COLUMNS = (
    "experiment_id",
    "condition_id",
    "seed",
    "status",
    "failure_type",
    "failure_message",
)


def experiment_summary_rows(results: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    """`results` is a sequence of `ExperimentResult.to_dict()`-shaped
    mappings. Failed/extinct runs are included, never dropped (Phase
    14's "do not hide failed runs")."""
    rows = []
    for result in results:
        rows.append(
            {
                "experiment_id": result.get("name"),
                "condition_id": result.get("condition_id"),
                "seed": result.get("seed"),
                "status": result.get("status"),
                "generations_completed": result.get("generations_completed"),
                "final_population_size": result.get("final_population_size"),
            }
        )
    return rows


def failed_run_rows(results: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for result in results:
        if result.get("status") not in ("failed", "extinct"):
            continue
        failure = result.get("failure") or {}
        rows.append(
            {
                "experiment_id": result.get("name"),
                "condition_id": result.get("condition_id"),
                "seed": result.get("seed"),
                "status": result.get("status"),
                "failure_type": failure.get("type"),
                "failure_message": failure.get("message"),
            }
        )
    return rows


__all__ = [
    "to_csv",
    "to_markdown",
    "to_latex",
    "EXPERIMENT_SUMMARY_COLUMNS",
    "CONDITION_SUMMARY_COLUMNS",
    "FAILED_RUN_COLUMNS",
    "experiment_summary_rows",
    "failed_run_rows",
]
