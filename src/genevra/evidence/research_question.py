"""Phase 19.2/19.3: research questions as structured, linkable records.

A `ResearchQuestion` never assumes its own answer. `evidence_status`
starts as `NOT_TESTED` and is only ever set by whatever code path
actually ran the corresponding experiment and computed the corresponding
statistic — nothing in this module infers a status from a description.
"""

from __future__ import annotations

import dataclasses
from dataclasses import dataclass
from enum import StrEnum
from typing import Any


class EvidenceStatus(StrEnum):
    SUPPORTED = "SUPPORTED"
    PARTIALLY_SUPPORTED = "PARTIALLY_SUPPORTED"
    INCONCLUSIVE = "INCONCLUSIVE"
    NOT_SUPPORTED = "NOT_SUPPORTED"
    CONTRADICTED = "CONTRADICTED"
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"
    NOT_TESTED = "NOT_TESTED"


@dataclass(frozen=True)
class ResearchQuestion:
    question_id: str
    title: str
    description: str
    hypothesis_ids: tuple[str, ...]
    primary_outcome: str
    secondary_outcomes: tuple[str, ...]
    experimental_conditions: tuple[str, ...]
    required_replication: int
    statistical_plan: str
    evidence_status: EvidenceStatus
    limitations: tuple[str, ...]
    experiment_ids: tuple[str, ...] = ()
    """Which `research_evidence/experiments/*` entries this RQ's status
    is actually based on — empty when `evidence_status` is `NOT_TESTED`."""

    def to_dict(self) -> dict[str, Any]:
        payload = dataclasses.asdict(self)
        payload["evidence_status"] = self.evidence_status.value
        return payload


__all__ = ["EvidenceStatus", "ResearchQuestion"]
