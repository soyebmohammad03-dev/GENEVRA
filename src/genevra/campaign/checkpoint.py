"""Phase 17.4: campaign/run checkpointing and resume.

One JSON file (`runs/checkpoint.json`) tracks the status of every
(condition, replicate) cell in a campaign. `CampaignCheckpoint.load_or_create`
is what makes a campaign resumable: calling it twice against the same
`output_root`/`campaign_id` returns a checkpoint that already knows which
cells are `COMPLETED` (or `FAILED`, which is also final — a failed run is
never silently retried into a second, different result) and which are
still `PENDING`. `CampaignRunner` (see `runner.py`) is the only thing that
should ever call `mark_running`/`mark_completed`/`mark_failed`.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from typing import Any


class RunStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    INTERRUPTED = "interrupted"


@dataclass
class RunRecord:
    condition_id: str
    replicate_index: int
    seed: int
    status: RunStatus
    error: str | None = None
    updated_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())

    def to_dict(self) -> dict[str, Any]:
        return {
            "condition_id": self.condition_id,
            "replicate_index": self.replicate_index,
            "seed": self.seed,
            "status": self.status.value,
            "error": self.error,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> RunRecord:
        return cls(
            condition_id=data["condition_id"],
            replicate_index=data["replicate_index"],
            seed=data["seed"],
            status=RunStatus(data["status"]),
            error=data.get("error"),
            updated_at=data.get("updated_at", ""),
        )


def _key(condition_id: str, replicate_index: int) -> str:
    return f"{condition_id}::{replicate_index}"


@dataclass
class CampaignCheckpoint:
    path: Path
    runs: dict[str, RunRecord] = field(default_factory=dict)

    @classmethod
    def load_or_create(cls, path: Path) -> CampaignCheckpoint:
        """Any run left `RUNNING` from a prior process (killed mid-run,
        machine restart) is marked `INTERRUPTED` on load — it is not
        silently treated as completed, and `is_pending` below returns
        `True` for it so the next `CampaignRunner.run()` call redoes it."""
        if not path.exists():
            return cls(path=path)
        raw = json.loads(path.read_text())
        runs = {k: RunRecord.from_dict(v) for k, v in raw.items()}
        for record in runs.values():
            if record.status is RunStatus.RUNNING:
                record.status = RunStatus.INTERRUPTED
        checkpoint = cls(path=path, runs=runs)
        checkpoint.save()
        return checkpoint

    def save(self) -> None:
        self.path.write_text(json.dumps({k: v.to_dict() for k, v in self.runs.items()}, indent=2))

    def is_pending(self, condition_id: str, replicate_index: int) -> bool:
        record = self.runs.get(_key(condition_id, replicate_index))
        return record is None or record.status in (RunStatus.INTERRUPTED, RunStatus.PENDING)

    def mark_running(self, condition_id: str, replicate_index: int, seed: int) -> None:
        self.runs[_key(condition_id, replicate_index)] = RunRecord(
            condition_id, replicate_index, seed, RunStatus.RUNNING
        )
        self.save()

    def mark_completed(self, condition_id: str, replicate_index: int, seed: int) -> None:
        self.runs[_key(condition_id, replicate_index)] = RunRecord(
            condition_id, replicate_index, seed, RunStatus.COMPLETED
        )
        self.save()

    def mark_failed(self, condition_id: str, replicate_index: int, seed: int, error: str) -> None:
        self.runs[_key(condition_id, replicate_index)] = RunRecord(
            condition_id, replicate_index, seed, RunStatus.FAILED, error=error
        )
        self.save()

    def summary(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for record in self.runs.values():
            counts[record.status.value] = counts.get(record.status.value, 0) + 1
        return counts


__all__ = ["RunStatus", "RunRecord", "CampaignCheckpoint"]
