"""Phase 19.13: the machine-readable evidence manifest — one
`EvidenceArtifact` record per figure/table/report/data file under
`research_evidence/`, so every generated file traces back to the
research question, experiment, condition, and seed set that produced it.
"""

from __future__ import annotations

import dataclasses
import json
import subprocess
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


def _git_commit() -> str | None:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"], capture_output=True, text=True, timeout=5, check=False
        )
    except (OSError, subprocess.SubprocessError):  # pragma: no cover - environment-dependent
        return None
    return result.stdout.strip() if result.returncode == 0 else None


@dataclass(frozen=True)
class EvidenceArtifact:
    artifact_id: str
    artifact_type: str
    """"figure" | "table" | "report" | "data" | "config" | "seeds"."""
    research_question: str
    experiment_id: str
    condition: str
    seed_set: tuple[int, ...]
    source_data: str
    metric_ids: tuple[str, ...]
    analysis_version: str
    config_hash: str
    relative_path: str
    limitations: tuple[str, ...] = ()
    git_commit: str | None = field(default_factory=_git_commit)
    creation_timestamp: str = field(default_factory=lambda: datetime.now(UTC).isoformat())

    def to_dict(self) -> dict[str, Any]:
        return dataclasses.asdict(self)


@dataclass
class EvidenceManifest:
    artifacts: list[EvidenceArtifact] = field(default_factory=list)

    def add(self, artifact: EvidenceArtifact) -> None:
        self.artifacts.append(artifact)

    def to_dict(self) -> dict[str, Any]:
        return {"artifacts": [a.to_dict() for a in self.artifacts]}

    def save(self, path: Path) -> None:
        path.write_text(json.dumps(self.to_dict(), indent=2))

    @classmethod
    def load(cls, path: Path) -> EvidenceManifest:
        data = json.loads(path.read_text())
        artifacts = []
        for raw in data["artifacts"]:
            payload = dict(raw)
            payload["seed_set"] = tuple(payload["seed_set"])
            payload["metric_ids"] = tuple(payload["metric_ids"])
            payload["limitations"] = tuple(payload.get("limitations", ()))
            artifacts.append(EvidenceArtifact(**payload))
        return cls(artifacts=artifacts)


__all__ = ["EvidenceArtifact", "EvidenceManifest"]
