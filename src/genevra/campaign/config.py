"""Phase 17.1/17.2/17.8: the campaign configuration and pre-registration
plan, following `genevra.literature.spec.LiteratureExperimentSpec`'s
structured-field/frozen-before-execution convention.

`CampaignConfig` does not embed condition factories (arbitrary Python
callables aren't JSON-serializable) — it names conditions by ID and
records `n_replicates`/`mode`; the caller supplies the actual
`{condition_id: seed -> result}` callables to `CampaignRunner.run`, the
same "spec is reproducible given its JSON plus the checked-in Python that
defines its factories" contract `LiteratureExperimentSpec` already uses.
"""

from __future__ import annotations

import dataclasses
import hashlib
import json
import subprocess
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Any


class CampaignMode(StrEnum):
    PILOT = "pilot"
    STANDARD = "standard"
    RESEARCH = "research"


_MODE_DEFAULT_SEEDS: dict[CampaignMode, int] = {
    CampaignMode.PILOT: 4,
    CampaignMode.STANDARD: 12,
    CampaignMode.RESEARCH: 24,
}


def _git_commit() -> str | None:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"], capture_output=True, text=True, timeout=5, check=False
        )
    except (OSError, subprocess.SubprocessError):  # pragma: no cover - environment-dependent
        return None
    return result.stdout.strip() if result.returncode == 0 else None


def _config_hash(payload: dict[str, Any]) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()[:16]


@dataclass(frozen=True)
class AnalysisPlan:
    """Frozen *before* a campaign runs (Phase 17.8) and only ever
    consumed, never regenerated, by `CampaignReport` — the file on disk
    under `.../analysis_plan.json` is the one this dataclass wrote, not
    something reconstructed after looking at results."""

    primary_outcome: str
    secondary_outcomes: tuple[str, ...]
    expected_direction: str
    comparison: str
    statistical_test: str
    replication_unit: str = "seed"
    exclusion_criteria: tuple[str, ...] = ()
    min_sample_size: int = 3

    def __post_init__(self) -> None:
        if self.expected_direction not in ("positive", "negative", "undirected"):
            raise ValueError("expected_direction must be 'positive', 'negative', or 'undirected'")
        if self.replication_unit != "seed":
            raise ValueError(
                "replication_unit must be 'seed' — organisms/generations are not "
                "independent replicates (Phase 16.1/17.6)"
            )
        if self.min_sample_size < 2:
            raise ValueError("min_sample_size must be >= 2")

    def to_dict(self) -> dict[str, Any]:
        return dataclasses.asdict(self)

    def save(self, path: Path) -> None:
        path.write_text(json.dumps(self.to_dict(), indent=2))

    @classmethod
    def load(cls, path: Path) -> AnalysisPlan:
        data = json.loads(path.read_text())
        data["secondary_outcomes"] = tuple(data["secondary_outcomes"])
        data["exclusion_criteria"] = tuple(data.get("exclusion_criteria", ()))
        return cls(**data)


@dataclass(frozen=True)
class CampaignConfig:
    campaign_id: str
    research_question: str
    hypotheses: tuple[str, ...]
    condition_ids: tuple[str, ...]
    mode: CampaignMode
    n_replicates: int
    campaign_seed: int
    analysis_plan: AnalysisPlan
    population_size: int
    generations_or_steps: int
    worker_count: int = 1
    notes: str = ""

    def __post_init__(self) -> None:
        if not self.condition_ids:
            raise ValueError("condition_ids must be non-empty")
        if len(set(self.condition_ids)) != len(self.condition_ids):
            raise ValueError("condition_ids must be unique")
        if self.n_replicates < 1:
            raise ValueError("n_replicates must be positive")
        if self.worker_count < 1:
            raise ValueError("worker_count must be positive")

    def to_dict(self) -> dict[str, Any]:
        payload = dataclasses.asdict(self)
        payload["analysis_plan"] = self.analysis_plan.to_dict()
        return payload

    def config_hash(self) -> str:
        return _config_hash(self.to_dict())

    def manifest(self) -> dict[str, Any]:
        """What `CampaignBundle` writes to `manifest.json` — the config
        plus the two facts that make a manifest a manifest rather than
        just a config dump: the exact code version and a hash of the
        config it describes, so a later reader can tell whether the code
        that produced a result has since changed."""
        return {
            **self.to_dict(),
            "config_hash": self.config_hash(),
            "git_commit": _git_commit(),
        }

    def budget_summary(self) -> dict[str, Any]:
        """Phase 18.19-style budget estimate — shown before a campaign
        launches so a large workload is never launched silently."""
        n_conditions = len(self.condition_ids)
        n_runs = n_conditions * self.n_replicates
        return {
            "conditions": n_conditions,
            "replicates_per_condition": self.n_replicates,
            "total_runs": n_runs,
            "generations_or_steps_per_run": self.generations_or_steps,
            "estimated_total_simulation_steps": n_runs * self.generations_or_steps,
            "worker_count": self.worker_count,
        }


def default_n_replicates(mode: CampaignMode) -> int:
    return _MODE_DEFAULT_SEEDS[mode]


__all__ = ["CampaignMode", "AnalysisPlan", "CampaignConfig", "default_n_replicates"]
