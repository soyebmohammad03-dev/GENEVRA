"""Phase 14.10: the automated research report bundle's report text,
following the `to_dict()`/`to_text()` convention shared by every other
GENEVRA report (`genevra.discovery.report`, `genevra.literature.report`,
`genevra.innovation.report`). This report transcludes/summarizes
existing reports (discovery/literature/innovation) rather than
re-deriving their prose.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from genevra.artifacts.index import ResearchArtifactIndex
from genevra.artifacts.style import FigureMetadata

_SAFEGUARD_NOTE = (
    "This report distinguishes association from causation, potential from realized "
    "outcomes, and exploratory from confirmatory analysis throughout. No figure, "
    "table, or metric here should be read as establishing a causal mechanism or a "
    "final scientific conclusion — see each section's own limitations."
)


@dataclass(frozen=True)
class ArtifactReportBundle:
    experiment_id: str
    research_question: str
    conditions: tuple[str, ...]
    seeds: tuple[int, ...]
    metrics_used: tuple[str, ...]
    statistical_methods: tuple[str, ...]
    main_results_summary: str
    figures: tuple[FigureMetadata, ...]
    table_names: tuple[str, ...]
    alternative_explanations_summary: str
    limitations: tuple[str, ...]
    reproduction_status: str
    replication_status: str
    open_endedness_evidence_summary: str
    index: ResearchArtifactIndex
    safeguards: str = field(default=_SAFEGUARD_NOTE)

    def to_dict(self) -> dict[str, Any]:
        return {
            "experiment_id": self.experiment_id,
            "research_question": self.research_question,
            "conditions": list(self.conditions),
            "seeds": list(self.seeds),
            "metrics_used": list(self.metrics_used),
            "statistical_methods": list(self.statistical_methods),
            "main_results_summary": self.main_results_summary,
            "figures": [f.to_dict() for f in self.figures],
            "table_names": list(self.table_names),
            "alternative_explanations_summary": self.alternative_explanations_summary,
            "limitations": list(self.limitations),
            "reproduction_status": self.reproduction_status,
            "replication_status": self.replication_status,
            "open_endedness_evidence_summary": self.open_endedness_evidence_summary,
            "index": self.index.to_dict(),
            "safeguards": self.safeguards,
        }

    def to_text(self) -> str:
        lines = [f"# Research Report Bundle: {self.experiment_id}", ""]
        lines.append("## 1. Research Question")
        lines.append(self.research_question)
        lines.append("")
        lines.append("## 2-3. Experimental Design / Conditions")
        lines.append(f"conditions={list(self.conditions)}")
        lines.append("")
        lines.append("## 4. Seeds")
        lines.append(f"seeds={list(self.seeds)} (n={len(self.seeds)})")
        lines.append("")
        lines.append("## 5-6. Metrics / Statistical Methods")
        lines.append(f"metrics={list(self.metrics_used)}")
        lines.append(f"statistical_methods={list(self.statistical_methods)}")
        lines.append("")
        lines.append("## 7. Main Results")
        lines.append(self.main_results_summary)
        lines.append("")
        lines.append("## 8. Figures")
        for figure in self.figures:
            lines.append(f"- {figure.figure_id}: {figure.caption}")
        lines.append("")
        lines.append("## 9. Tables")
        for name in self.table_names:
            lines.append(f"- {name}")
        lines.append("")
        lines.append("## 10. Alternative Explanations")
        lines.append(self.alternative_explanations_summary)
        lines.append("")
        lines.append("## 11. Limitations")
        for limitation in self.limitations:
            lines.append(f"- {limitation}")
        lines.append("")
        lines.append("## 12. Reproduction Status")
        lines.append(self.reproduction_status)
        lines.append("")
        lines.append("## 13. Replication Status")
        lines.append(self.replication_status)
        lines.append("")
        lines.append("## 14. Open-Endedness Evidence")
        lines.append(self.open_endedness_evidence_summary)
        lines.append("")
        lines.append("## 15. Scientific-Language Safeguards")
        lines.append(self.safeguards)
        lines.append("")
        lines.append("## Research Artifact Index")
        lines.append(self.index.to_text())
        return "\n".join(lines)


__all__ = ["ArtifactReportBundle"]
