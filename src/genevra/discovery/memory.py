"""Phase 10.9: a persistent, structured scientific-provenance record —
not chatbot memory. `ResearchMemory` stores typed `ResearchRecord`s
(experiments, hypotheses, observations/phenomena, follow-up proposals,
conclusions) linked by explicit `parent_ids`, so a chain like
"Observation A -> Hypothesis H -> Experiment E -> Result R -> Follow-up F"
is traceable by walking `parent_ids`/`children`, and persisted to a plain
JSON file rather than requiring a database the rest of this codebase does
not otherwise need.
"""

from __future__ import annotations

import dataclasses
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

RecordType = Literal[
    "phenomenon",
    "anomaly",
    "correlation",
    "hypothesis",
    "followup",
    "experiment_result",
    "conclusion",
    "contradiction",
]


@dataclass(frozen=True)
class ResearchRecord:
    record_id: str
    record_type: RecordType
    payload: dict[str, Any]
    parent_ids: tuple[str, ...] = ()
    """The record(s) this one was derived from — e.g. a `"hypothesis"`
    record's `parent_ids` would name the `"phenomenon"`/`"correlation"`
    records that generated it. Empty for a root record (e.g. a raw
    experiment result)."""


@dataclass
class ResearchMemory:
    """An in-process store, `save()`d to and `load()`ed from a single
    JSON file (a plain list of records) — the smallest persistence
    mechanism that satisfies "structured record," not a database engine
    this project does not otherwise need."""

    records: dict[str, ResearchRecord] = field(default_factory=dict)

    def add(self, record: ResearchRecord) -> None:
        if record.record_id in self.records:
            raise ValueError(f"record {record.record_id!r} already exists")
        self.records[record.record_id] = record

    def get(self, record_id: str) -> ResearchRecord:
        return self.records[record_id]

    def by_type(self, record_type: RecordType) -> list[ResearchRecord]:
        return [r for r in self.records.values() if r.record_type == record_type]

    def children(self, record_id: str) -> list[ResearchRecord]:
        return [r for r in self.records.values() if record_id in r.parent_ids]

    def trace_lineage(self, record_id: str) -> list[ResearchRecord]:
        """The full ancestor chain back to root record(s), earliest
        first — the "Observation A -> Hypothesis H -> ..." graph
        flattened to one record's provenance path. Uses the first parent
        when a record has more than one (e.g. a correlation-derived
        hypothesis with two contributing observations); `parent_ids`
        itself still records every parent."""
        chain: list[ResearchRecord] = []
        current = self.records.get(record_id)
        seen: set[str] = set()
        while current is not None and current.record_id not in seen:
            chain.append(current)
            seen.add(current.record_id)
            current = self.records.get(current.parent_ids[0]) if current.parent_ids else None
        chain.reverse()
        return chain

    def save(self, path: Path) -> None:
        payload = [dataclasses.asdict(record) for record in self.records.values()]
        path.write_text(json.dumps(payload, indent=2))

    @classmethod
    def load(cls, path: Path) -> ResearchMemory:
        raw = json.loads(path.read_text())
        memory = cls()
        for entry in raw:
            memory.add(
                ResearchRecord(
                    record_id=entry["record_id"],
                    record_type=entry["record_type"],
                    payload=entry["payload"],
                    parent_ids=tuple(entry.get("parent_ids", ())),
                )
            )
        return memory


__all__ = ["RecordType", "ResearchRecord", "ResearchMemory"]
