"""Controlled comparisons: run the same set of seeds across two or more
named conditions, so a comparison's only intentional variable is whatever
the condition factories actually differ in.

The seed sequence is shared across conditions by construction — `run()`
calls `condition_factory(seed)` for the same `seeds` list under every
condition name, so "condition A, seed 3" and "condition B, seed 3" start
from the same environment/organism/RNG seed and differ only in whatever
the two factory functions actually configure differently. This is what
makes a comparison controlled rather than confounded: if condition B's
factory accidentally used a different seed policy, this class would not
catch that mistake, so the burden is on the config factories the caller
supplies — documented here rather than silently assumed.
"""

from __future__ import annotations

import concurrent.futures
import multiprocessing
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import Any

from genevra.experiments.config import ExperimentConfig
from genevra.experiments.runner import ExperimentRunner


@dataclass(frozen=True)
class ComparisonResult:
    conditions: dict[str, list[dict[str, Any]]]
    seeds: tuple[int, ...]

    def failures(self) -> list[dict[str, Any]]:
        """Every run across every condition whose status is `"failed"` —
        surfaced explicitly rather than silently absent from `conditions`."""
        return [
            result
            for results in self.conditions.values()
            for result in results
            if result["status"] == "failed"
        ]


@dataclass(frozen=True)
class ComparisonRunner:
    conditions: dict[str, Callable[[int], ExperimentConfig]]
    seeds: Sequence[int]

    def __post_init__(self) -> None:
        if not self.conditions:
            raise ValueError("at least one condition is required")
        if not self.seeds:
            raise ValueError("at least one seed is required")

    def run(self, parallel: bool = False, max_workers: int | None = None) -> ComparisonResult:
        """Runs every (condition, seed) pair. `parallel=False` (default)
        is the sequential reference mode. `parallel=True` runs each
        (condition, seed) pair in its own OS process
        (`ProcessPoolExecutor`, `fork` start method — see module note
        below): each run builds and owns a fresh `ExperimentConfig` and
        `EvolutionEngine` with its own `np.random.Generator` seeded from
        that run's own seed, so there is no shared mutable simulation
        state and no global RNG between runs, whether sequential or
        parallel. A run that raises is caught by `ExperimentRunner.run()`
        itself (`status="failed"`) and cannot corrupt any other run's
        result; results are always returned keyed by their originating
        condition name and seed, so identity is never lost or mixed up
        across processes.

        `parallel=True` requires every `EvolutionConfig` component
        (fitness function, selection strategy, mutation operator,
        `learning_rule_factory`, etc.) to be a module-level class or
        function, not a lambda or locally-defined closure — those cannot
        be pickled to send to a worker process. This surfaces as a clear
        `pickle` error from the failing config, not a silent fallback.
        """
        if not parallel:
            conditions: dict[str, list[dict[str, Any]]] = {
                name: [
                    ExperimentRunner(factory(seed), condition_id=name).run().to_dict()
                    for seed in self.seeds
                ]
                for name, factory in self.conditions.items()
            }
            return ComparisonResult(conditions=conditions, seeds=tuple(self.seeds))

        jobs = [
            (name, seed, factory(seed))
            for name, factory in self.conditions.items()
            for seed in self.seeds
        ]
        # "fork" (not the platform default "spawn" on macOS) so pickling
        # only needs to cross the pipe for arguments/results, not the
        # whole interpreter state, without changing anything about run
        # semantics or determinism.
        context = multiprocessing.get_context("fork")
        results_by_condition: dict[str, dict[int, dict[str, Any]]] = {
            name: {} for name in self.conditions
        }
        with concurrent.futures.ProcessPoolExecutor(
            max_workers=max_workers, mp_context=context
        ) as executor:
            future_to_job = {
                executor.submit(_run_one, config, name): (name, seed) for name, seed, config in jobs
            }
            for future in concurrent.futures.as_completed(future_to_job):
                name, seed = future_to_job[future]
                results_by_condition[name][seed] = future.result()

        conditions = {
            name: [results_by_condition[name][seed] for seed in self.seeds]
            for name in self.conditions
        }
        return ComparisonResult(conditions=conditions, seeds=tuple(self.seeds))


def _run_one(config: ExperimentConfig, condition_id: str) -> dict[str, Any]:
    """Module-level (picklable-by-reference) unit of work for the
    parallel executor: builds and runs one fully independent
    `ExperimentRunner` inside the worker process."""
    return ExperimentRunner(config, condition_id=condition_id).run().to_dict()


@dataclass(frozen=True)
class ComparisonValidation:
    """Phase 8.17 scientific safety rails. `errors` are critical
    incompatibilities that make a cross-condition comparison unsound
    (e.g. conditions run over different seed sets, so "condition A" and
    "condition B" were never actually controlled against the same
    starting conditions) — callers should treat a non-empty `errors` as
    a reason not to trust aggregate statistics computed over the result.
    `warnings` are visible but non-fatal irregularities (a failed run
    mixed into completed ones, mismatched software versions, runs that
    completed a different number of generations) that a researcher
    should see before interpreting results, but that don't make the
    comparison meaningless outright."""

    errors: tuple[str, ...]
    warnings: tuple[str, ...]

    def ok(self) -> bool:
        return not self.errors


def validate_comparison(result: ComparisonResult) -> ComparisonValidation:
    errors: list[str] = []
    warnings: list[str] = []

    run_counts = {name: len(runs) for name, runs in result.conditions.items()}
    if len(set(run_counts.values())) > 1:
        errors.append(f"conditions have different numbers of runs: {run_counts}")

    for name, runs in result.conditions.items():
        seeds_seen = {r["seed"] for r in runs}
        missing = set(result.seeds) - seeds_seen
        if missing:
            errors.append(f"condition {name!r} is missing runs for seeds {sorted(missing)}")

        failed = [r for r in runs if r["status"] == "failed"]
        if failed:
            warnings.append(
                f"condition {name!r} has {len(failed)} failed run(s) out of {len(runs)} "
                "— never silently treat these as successful in aggregate statistics"
            )

        versions = {r["software"]["genevra_version"] for r in runs}
        if len(versions) > 1:
            warnings.append(f"condition {name!r} mixes software versions: {sorted(versions)}")

        completed_generation_counts = {
            r["generations_completed"] for r in runs if r["status"] == "completed"
        }
        if len(completed_generation_counts) > 1:
            warnings.append(
                f"condition {name!r} has completed runs with differing generation counts "
                f"{sorted(completed_generation_counts)} — trajectories are not directly "
                "comparable generation-by-generation without accounting for this"
            )

        environment_summaries = {
            repr(sorted(r["environment_summary"].items())) for r in runs if r["status"] != "failed"
        }
        if len(environment_summaries) > 1:
            warnings.append(
                f"condition {name!r} runs use different environment configurations across seeds"
            )

    return ComparisonValidation(errors=tuple(errors), warnings=tuple(warnings))
