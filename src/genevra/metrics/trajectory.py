"""A structured, serializable per-generation history.

`GenerationSnapshot` is an explicit schema (not an arbitrary object graph)
so a `Trajectory` can be exported to JSON (`to_dict()` produces plain
dicts/lists/primitives) or, later, CSV/Parquet without redesigning
storage. This is the data model evolutionary-change measurements (genome/
behavior centroid shift across generations, diversity trajectory,
extinction) are read from.
"""

from __future__ import annotations

import dataclasses
from dataclasses import dataclass
from typing import Any

from genevra.metrics.fitness_metrics import FitnessSummary


@dataclass(frozen=True)
class GenerationSnapshot:
    """`mean_novelty` is *cumulative/historical* novelty: each
    individual's behavioral signature scored against the persistent
    cross-generation `NoveltyArchive` (built up over the whole run so
    far), then averaged. `instantaneous_novelty` is scored only against
    this generation's own signatures (leave-one-out), ignoring history —
    "how different are individuals from their current peers" rather than
    "how different from everything seen so far." See docs/metrics.md."""

    generation: int
    fitness_summary: FitnessSummary
    genotypic_diversity: float
    behavioral_diversity: float
    mean_novelty: float
    instantaneous_novelty: float
    survival_rate: float
    reproductive_success_rate: float
    mean_mutation_rate: float
    mean_mutation_sigma: float
    genome_centroid_shift: float | None
    behavior_centroid_shift: float | None
    extinction: bool


class Trajectory:
    def __init__(self) -> None:
        self.snapshots: list[GenerationSnapshot] = []

    def append(self, snapshot: GenerationSnapshot) -> None:
        self.snapshots.append(snapshot)

    def to_dict(self) -> list[dict[str, Any]]:
        return [dataclasses.asdict(snapshot) for snapshot in self.snapshots]

    def __len__(self) -> int:
        return len(self.snapshots)
