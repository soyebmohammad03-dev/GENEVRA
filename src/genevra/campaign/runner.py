"""Phase 17.4/17.5/17.15: `CampaignRunner` — executes
`condition x replicate` cells against a caller-supplied `run_fn`, skipping
cells the checkpoint already marks `COMPLETED`/`FAILED` (resume), isolating
one cell's exception from every other cell (failure-aware: a failed run
is recorded and the campaign continues), and writing each cell's raw
result to `runs/<condition_id>/<replicate_index>.json` so no individual
run is ever discarded in favor of only an aggregate.

Parallelism (17.5): `worker_count > 1` uses
`concurrent.futures.ProcessPoolExecutor`, mirroring the pattern
`genevra.experiments.runner`/`ComparisonRunner` already use for
independent-seed parallelism — one process per cell, no shared mutable
state, and a worker's exception is caught and recorded as a failed run
rather than crashing the whole campaign.
"""

from __future__ import annotations

import json
import traceback
from collections.abc import Callable, Mapping
from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from genevra.campaign.checkpoint import CampaignCheckpoint
from genevra.campaign.config import CampaignConfig
from genevra.campaign.seeding import derive_condition_seeds, derive_replicate_seeds

RunFn = Callable[[str, int, int], dict[str, Any]]
"""`(condition_id, seed, replicate_index) -> a JSON-serializable result
dict`. Raising is caught by the runner and recorded as a failed cell."""


@dataclass(frozen=True)
class CampaignRunResult:
    completed: dict[str, dict[int, dict[str, Any]]]
    """`{condition_id: {replicate_index: result}}` for every cell that
    completed successfully — includes cells completed by this call *and*
    cells that were already `COMPLETED` from a prior interrupted run,
    reloaded from disk (resume never loses a previously-completed run's
    data)."""
    failed: dict[str, dict[int, str]]
    """`{condition_id: {replicate_index: error string}}`."""
    requested_seeds: dict[str, list[int]]
    completed_seeds: dict[str, list[int]]
    failed_seeds: dict[str, list[int]]

    def to_dict(self) -> dict[str, Any]:
        return {
            "completed_counts": {c: len(v) for c, v in self.completed.items()},
            "failed_counts": {c: len(v) for c, v in self.failed.items()},
            "requested_seeds": self.requested_seeds,
            "completed_seeds": self.completed_seeds,
            "failed_seeds": self.failed_seeds,
        }


def _run_cell(
    run_fn: RunFn, condition_id: str, seed: int, replicate_index: int
) -> tuple[str, int, int, dict[str, Any] | None, str | None]:
    try:
        return (
            condition_id,
            replicate_index,
            seed,
            run_fn(condition_id, seed, replicate_index),
            None,
        )
    except Exception:  # noqa: BLE001 - a failed cell must not crash the campaign
        return condition_id, replicate_index, seed, None, traceback.format_exc()


class CampaignRunner:
    def __init__(self, config: CampaignConfig, runs_dir: Path) -> None:
        self.config = config
        self.runs_dir = runs_dir
        self.runs_dir.mkdir(parents=True, exist_ok=True)
        self.checkpoint = CampaignCheckpoint.load_or_create(runs_dir / "checkpoint.json")

    def _run_path(self, condition_id: str, replicate_index: int) -> Path:
        d = self.runs_dir / condition_id
        d.mkdir(parents=True, exist_ok=True)
        return d / f"{replicate_index}.json"

    def run(self, run_fn: RunFn) -> CampaignRunResult:
        condition_seeds = dict(
            zip(
                self.config.condition_ids,
                derive_condition_seeds(self.config.campaign_seed, len(self.config.condition_ids)),
                strict=True,
            )
        )
        cells: list[tuple[str, int, int]] = []
        for condition_id in self.config.condition_ids:
            replicate_seeds = derive_replicate_seeds(
                condition_seeds[condition_id], self.config.n_replicates
            )
            for replicate_index, seed in enumerate(replicate_seeds):
                if self.checkpoint.is_pending(condition_id, replicate_index):
                    cells.append((condition_id, seed, replicate_index))

        completed: dict[str, dict[int, dict[str, Any]]] = {c: {} for c in self.config.condition_ids}
        failed: dict[str, dict[int, str]] = {c: {} for c in self.config.condition_ids}
        # Reload already-completed cells from disk so resume returns the
        # full picture, not only what this call itself executed.
        for record in self.checkpoint.runs.values():
            if record.status.value == "completed":
                path = self._run_path(record.condition_id, record.replicate_index)
                if path.exists():
                    completed[record.condition_id][record.replicate_index] = json.loads(
                        path.read_text()
                    )
            elif record.status.value == "failed":
                failed[record.condition_id][record.replicate_index] = record.error or ""

        for condition_id, seed, replicate_index in cells:
            self.checkpoint.mark_running(condition_id, replicate_index, seed)

        if self.config.worker_count > 1 and cells:
            with ProcessPoolExecutor(max_workers=self.config.worker_count) as pool:
                futures = [
                    pool.submit(_run_cell, run_fn, cid, seed, ridx) for cid, seed, ridx in cells
                ]
                outcomes = [f.result() for f in futures]
        else:
            outcomes = [_run_cell(run_fn, cid, seed, ridx) for cid, seed, ridx in cells]

        for condition_id, replicate_index, seed, result, error in outcomes:
            if error is None and result is not None:
                self._run_path(condition_id, replicate_index).write_text(
                    json.dumps(result, indent=2)
                )
                completed[condition_id][replicate_index] = result
                self.checkpoint.mark_completed(condition_id, replicate_index, seed)
            else:
                failed[condition_id][replicate_index] = error or "unknown error"
                self.checkpoint.mark_failed(condition_id, replicate_index, seed, error or "")

        requested_seeds = {
            cid: derive_replicate_seeds(condition_seeds[cid], self.config.n_replicates)
            for cid in self.config.condition_ids
        }
        completed_seeds = {
            cid: [requested_seeds[cid][i] for i in sorted(completed[cid])]
            for cid in self.config.condition_ids
        }
        failed_seeds = {
            cid: [requested_seeds[cid][i] for i in sorted(failed[cid])]
            for cid in self.config.condition_ids
        }
        return CampaignRunResult(
            completed=completed,
            failed=failed,
            requested_seeds=requested_seeds,
            completed_seeds=completed_seeds,
            failed_seeds=failed_seeds,
        )


def condition_values(
    run_result: CampaignRunResult, condition_id: str, metric_path: str
) -> Mapping[int, float]:
    """Extract one scalar metric per completed replicate for one
    condition, keyed by replicate index (not seed — callers that need
    seed-keyed values should zip against `run_result.completed_seeds`).
    Missing/non-numeric values are dropped, never defaulted."""
    values: dict[int, float] = {}
    for replicate_index, result in run_result.completed[condition_id].items():
        node: Any = result
        for part in metric_path.split("."):
            if isinstance(node, dict) and part in node:
                node = node[part]
            else:
                node = None
                break
        try:
            if node is not None:
                values[replicate_index] = float(node)
        except (TypeError, ValueError):
            continue
    return values


__all__ = ["RunFn", "CampaignRunResult", "CampaignRunner", "condition_values"]
