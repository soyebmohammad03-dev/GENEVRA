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
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from genevra.metrics.distribution import DistributionSummary
from genevra.metrics.fitness_metrics import FitnessSummary


class MetricsLevel(Enum):
    """How much per-generation metric computation `EvolutionEngine` does
    (Phase 7.4). Every level always computes fitness (needed for
    selection itself, not optional instrumentation).

    - `MINIMAL`: fitness and survival/reproductive-success only — skips
      behavioral signatures, novelty, diversity, and centroid shift, for
      long exploratory runs where only the fitness trajectory matters.
    - `STANDARD` (default): everything Phase 1-6 already computed
      (novelty, diversity, centroid shift), capped by
      `EvolutionConfig.diversity_max_pairs` when set.
    - `RESEARCH`: `STANDARD` plus per-generation learning-strategy
      distribution statistics (`learning_gene_stats`), computed only
      every `EvolutionConfig.metrics_interval` generations (other
      generations at `RESEARCH` fall back to `STANDARD` computation) —
      research-only detail is not free, so its cost is bounded
      explicitly rather than paid every generation by default.
    """

    MINIMAL = "minimal"
    STANDARD = "standard"
    RESEARCH = "research"


@dataclass(frozen=True)
class GenerationSnapshot:
    """`mean_novelty` is *cumulative/historical* novelty: each
    individual's behavioral signature scored against the persistent
    cross-generation `NoveltyArchive` (built up over the whole run so
    far), then averaged. `instantaneous_novelty` is scored only against
    this generation's own signatures (leave-one-out), ignoring history —
    "how different are individuals from their current peers" rather than
    "how different from everything seen so far." See docs/metrics.md.

    `learning_gene_stats`, when present (RESEARCH metrics level, on its
    sampled generations), is one `DistributionSummary` per heritable
    learning gene (index-aligned with `genome.learning_genes`:
    learning_rate, plasticity_gate, decay — see
    `genevra.organism.learning.LearningParams`), so a population that
    splits into two co-existing strategies (e.g. high- and low-plasticity)
    is visible in the quantiles even when the mean looks unremarkable.

    `eval_fitness_summary`, when present, is fitness measured on a
    *held-out* evaluation environment the population was never selected
    on this generation (Phase 8.4 generalization) — never conflated with
    `fitness_summary`, which is always the training-environment fitness
    selection actually acted on.
    """

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
    learning_gene_stats: tuple[DistributionSummary, ...] | None = None
    eval_fitness_summary: FitnessSummary | None = None
    metrics_level: str = field(default=MetricsLevel.STANDARD.value)


class Trajectory:
    def __init__(self) -> None:
        self.snapshots: list[GenerationSnapshot] = []

    def append(self, snapshot: GenerationSnapshot) -> None:
        self.snapshots.append(snapshot)

    def to_dict(self) -> list[dict[str, Any]]:
        return [dataclasses.asdict(snapshot) for snapshot in self.snapshots]

    def __len__(self) -> int:
        return len(self.snapshots)
