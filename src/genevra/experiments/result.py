"""A self-contained, JSON-serializable experiment result: identity
(name, condition, seed), software version metadata, environment summary,
the full metric trajectory, lineage records, and final population/run
status — including explicit failure information when a run raised, rather
than losing the run silently. Enough to know what produced a result and
to reproduce it, without dumping arbitrary simulation state."""

from __future__ import annotations

import dataclasses
import sys
from dataclasses import dataclass, field
from typing import Any

import numpy

from genevra import __version__


@dataclass(frozen=True)
class SoftwareMetadata:
    genevra_version: str
    python_version: str
    numpy_version: str


def current_software_metadata() -> SoftwareMetadata:
    return SoftwareMetadata(
        genevra_version=__version__,
        python_version=sys.version.split()[0],
        numpy_version=numpy.__version__,
    )


@dataclass(frozen=True)
class ExperimentResult:
    """`status` is one of `"completed"`, `"extinct"`, or `"failed"`.
    `failure` is populated only for `"failed"` runs — an exception raised
    anywhere during `ExperimentRunner.run()` is caught and recorded here
    (type name + message), never left to crash a multi-run comparison
    (see `genevra.analysis.comparison.ComparisonRunner`)."""

    name: str
    seed: int
    status: str
    software: SoftwareMetadata
    trajectory: list[dict[str, Any]]
    lineage: list[dict[str, Any]]
    final_population_size: int
    generations_completed: int
    environment_summary: dict[str, Any] = field(default_factory=dict)
    condition_id: str | None = None
    failure: dict[str, str] | None = None

    def to_dict(self) -> dict[str, Any]:
        return dataclasses.asdict(self)
