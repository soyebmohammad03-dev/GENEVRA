"""A self-contained, JSON-serializable experiment result: configuration
identity (name, seed), software version metadata, the full metric
trajectory, lineage records, and final population/run status — enough to
know what produced a result and to reproduce it, without dumping arbitrary
simulation state."""

from __future__ import annotations

import dataclasses
import sys
from dataclasses import dataclass
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
    name: str
    seed: int
    status: str
    software: SoftwareMetadata
    trajectory: list[dict[str, Any]]
    lineage: list[dict[str, Any]]
    final_population_size: int
    generations_completed: int

    def to_dict(self) -> dict[str, Any]:
        return dataclasses.asdict(self)
