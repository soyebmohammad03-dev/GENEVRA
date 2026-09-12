"""Phase 14.9: a structured, machine- and human-readable summary of what
research this run of GENEVRA has actually produced — not a graphical
dashboard, per the spec's explicit instruction. Built from
`ResearchMemory` counts (already the project's provenance store; not a
second query system) plus how many figures/tables this artifact bundle
wrote.
"""

from __future__ import annotations

import dataclasses
from dataclasses import dataclass
from typing import Any

from genevra.discovery.memory import ResearchMemory


@dataclass(frozen=True)
class ResearchArtifactIndex:
    experiment_count: int
    condition_count: int
    seed_count: int
    successful_runs: int
    failed_runs: int
    phenomena_count: int
    hypothesis_count: int
    replication_count: int
    figure_count: int
    table_count: int
    quality_gate_status: str

    def to_dict(self) -> dict[str, Any]:
        return dataclasses.asdict(self)

    def to_text(self) -> str:
        lines = ["# Research Artifact Index", ""]
        for field_ in dataclasses.fields(self):
            lines.append(f"{field_.name}: {getattr(self, field_.name)}")
        return "\n".join(lines)


def build_index(
    results: list[dict[str, Any]],
    memory: ResearchMemory | None,
    figure_count: int,
    table_count: int,
    quality_gate_status: str = "not_evaluated",
) -> ResearchArtifactIndex:
    condition_ids = {r.get("condition_id") for r in results if r.get("condition_id") is not None}
    seeds = {r.get("seed") for r in results}
    successful = sum(1 for r in results if r.get("status") == "completed")
    failed = sum(1 for r in results if r.get("status") in ("failed", "extinct"))

    phenomena = hypotheses = replications = 0
    if memory is not None:
        phenomena = len(memory.by_type("phenomenon")) + len(memory.by_type("anomaly"))
        hypotheses = len(memory.by_type("hypothesis"))
        replications = len([r for r in memory.records.values() if r.record_type == "conclusion"])

    return ResearchArtifactIndex(
        experiment_count=len(results),
        condition_count=len(condition_ids),
        seed_count=len(seeds),
        successful_runs=successful,
        failed_runs=failed,
        phenomena_count=phenomena,
        hypothesis_count=hypotheses,
        replication_count=replications,
        figure_count=figure_count,
        table_count=table_count,
        quality_gate_status=quality_gate_status,
    )


__all__ = ["ResearchArtifactIndex", "build_index"]
