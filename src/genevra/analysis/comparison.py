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

    def run(self) -> ComparisonResult:
        conditions: dict[str, list[dict[str, Any]]] = {}
        for condition_name, config_factory in self.conditions.items():
            results = []
            for seed in self.seeds:
                config = config_factory(seed)
                runner = ExperimentRunner(config, condition_id=condition_name)
                results.append(runner.run().to_dict())
            conditions[condition_name] = results
        return ComparisonResult(conditions=conditions, seeds=tuple(self.seeds))
