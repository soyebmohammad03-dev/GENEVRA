"""Phase 14.1: the standard research-artifact directory structure and a
provenance record linking every generated file back to its experiment
ID, configuration, seeds, code version, and metric/analysis versions.

`research_artifacts/` (the default root) is gitignored — see
`docs/research_artifacts.md`. Everything under it is reproducible
generated output, regenerated on demand from a stored `ExperimentResult`;
nothing here is a second source of truth for simulation data.
"""

from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

_SUBDIRS = (
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
)


def _git_commit() -> str | None:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"], capture_output=True, text=True, timeout=5, check=False
        )
    except (OSError, subprocess.SubprocessError):  # pragma: no cover - environment-dependent
        return None
    return result.stdout.strip() if result.returncode == 0 else None


@dataclass(frozen=True)
class ArtifactProvenance:
    experiment_id: str
    seeds: tuple[int, ...]
    configuration: dict[str, Any]
    git_commit: str | None
    metric_version: str
    analysis_version: str
    created_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())

    def to_dict(self) -> dict[str, Any]:
        return {
            "experiment_id": self.experiment_id,
            "seeds": list(self.seeds),
            "configuration": self.configuration,
            "git_commit": self.git_commit,
            "metric_version": self.metric_version,
            "analysis_version": self.analysis_version,
            "created_at": self.created_at,
        }


class ArtifactDirectory:
    """Creates and gives typed access to
    `<root>/<experiment_id>/{raw_data,derived_data,metrics,figures,tables,
    reports,provenance,configurations,seeds,logs,supplementary}/`.

    `extra_subdirs` (Phase 17.14) lets a campaign bundle add `conditions/`
    and `runs/` to the same tree without a second, parallel directory
    builder — pass `root=<root>/"campaigns"` and `experiment_id=campaign_id`
    to get `research_artifacts/campaigns/<campaign_id>/...`.
    """

    def __init__(self, root: Path, experiment_id: str, extra_subdirs: tuple[str, ...] = ()) -> None:
        self.experiment_id = experiment_id
        self.base = root / experiment_id
        for subdir in (*_SUBDIRS, *extra_subdirs):
            (self.base / subdir).mkdir(parents=True, exist_ok=True)

    @property
    def figures(self) -> Path:
        return self.base / "figures"

    @property
    def tables(self) -> Path:
        return self.base / "tables"

    @property
    def reports(self) -> Path:
        return self.base / "reports"

    @property
    def metrics(self) -> Path:
        return self.base / "metrics"

    @property
    def provenance_dir(self) -> Path:
        return self.base / "provenance"

    @property
    def configurations(self) -> Path:
        return self.base / "configurations"

    @property
    def seeds_dir(self) -> Path:
        return self.base / "seeds"

    @property
    def raw_data(self) -> Path:
        return self.base / "raw_data"

    def write_provenance(
        self,
        seeds: tuple[int, ...],
        configuration: dict[str, Any],
        metric_version: str = "genevra.metrics",
        analysis_version: str = "genevra.mechanisms.v1",
    ) -> ArtifactProvenance:
        provenance = ArtifactProvenance(
            experiment_id=self.experiment_id,
            seeds=seeds,
            configuration=configuration,
            git_commit=_git_commit(),
            metric_version=metric_version,
            analysis_version=analysis_version,
        )
        (self.provenance_dir / "provenance.json").write_text(
            json.dumps(provenance.to_dict(), indent=2)
        )
        (self.seeds_dir / "seeds.json").write_text(json.dumps(list(seeds), indent=2))
        (self.configurations / "configuration.json").write_text(json.dumps(configuration, indent=2))
        return provenance


__all__ = ["ArtifactDirectory", "ArtifactProvenance"]
