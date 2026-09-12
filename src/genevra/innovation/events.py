"""Phase 12.2: explicit `InnovationEvent` records.

**Innovation is not defined as "fitness increased."** An `InnovationEvent`
here is a birth whose heritable `LearningStrategy` (Phase 9's compact,
interpretable 3-tuple — see `genevra.analysis.learning_strategy`) is a
statistical outlier relative to its own generation's population: a
genuinely novel *strategy* appearing, kept as a separate measurement from
`fitness_effect` (Phase 12.2's explicit requirement — a behavior can be
novel without raising fitness, and fitness can rise without behavioral
novelty). `fitness_effect` is left `None` here: `LineageEvent` does not
record per-individual fitness, only birth/death/reproduction and the
learning-strategy snapshot, so this detector does not fabricate a number
it cannot measure — see `known_limitations` in
`genevra.innovation.report`.
"""

from __future__ import annotations

import dataclasses
from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Any

import numpy as np

from genevra.analysis.learning_strategy import LearningStrategy
from genevra.evolution.lineage import LineageEvent, LineageTracker

_LIMITATION_NOTE = (
    "An InnovationEvent flags a birth whose heritable learning strategy was a "
    "statistical outlier within its own generation's birth cohort. This is a "
    "structural novelty measurement, independent of fitness: fitness_effect is left "
    "None here because LineageEvent does not record per-individual fitness. A high "
    "novelty_score is not evidence the strategy was adaptive, and a strategy with a "
    "low novelty_score is not evidence it was unimportant."
)


@dataclass(frozen=True)
class InnovationEvent:
    event_id: str
    generation: int
    lineage: int
    """The individual id this event originates from (`LineageEvent.individual_id`)."""
    behavior_descriptor: tuple[float, float, float]
    """`(learning_rate, plasticity_gate, decay)` at birth — see
    `genevra.analysis.learning_strategy.LearningStrategy`."""
    novelty_score: float
    """A within-generation z-like score: this individual's strategy
    distance from its generation's mean strategy, divided by that
    generation's pooled strategy standard deviation. Not comparable across
    experiments with different strategy variance."""
    complexity_score: float | None = None
    """Not computed by this detector — GENEVRA has no complexity measure
    over learning strategies today; reserved for a future metric."""
    ecological_impact: float | None = None
    """Not computed by this detector — requires shared-ecology resource-
    competition data (`genevra.simulation.shared_grid_world`) this
    detector does not consume; reserved for a future metric."""
    persistence_duration: int | None = None
    """Generations survived (`death_generation - generation`), or `None`
    if still alive when the lineage record ends (right-censored, not
    "did not persist")."""
    descendant_count: int = 0
    fitness_effect: float | None = None
    environment: dict[str, Any] = field(default_factory=dict)
    provenance: tuple[str, ...] = ()
    limitation_note: str = field(default=_LIMITATION_NOTE)

    def to_dict(self) -> dict[str, Any]:
        return dataclasses.asdict(self)


def _descendant_count(tracker: LineageTracker, individual_id: int) -> int:
    """Total transitive descendants via breadth-first traversal of
    `LineageTracker.children` — a simple, correct (if O(n) per query)
    count; GENEVRA experiment population sizes make this laptop-feasible
    without a cached descendant index."""
    frontier = [individual_id]
    seen: set[int] = set()
    count = 0
    while frontier:
        current = frontier.pop()
        for child in tracker.children(current):
            if child in seen:
                continue
            seen.add(child)
            count += 1
            frontier.append(child)
    return count


def detect_innovation_events(
    lineage_events: Sequence[LineageEvent],
    tracker: LineageTracker,
    z_threshold: float = 2.0,
    min_cohort_size: int = 3,
) -> list[InnovationEvent]:
    """Groups `lineage_events` by birth generation; within any generation
    whose birth cohort has at least `min_cohort_size` individuals and
    non-zero strategy variance, flags individuals whose strategy distance
    from the cohort mean exceeds `z_threshold` pooled standard deviations.
    Generations with too few births, or with zero variance (every birth
    identical — e.g. `NoLearning`, where every strategy is the same fixed
    default), produce no events for that generation rather than dividing
    by zero."""
    if z_threshold <= 0:
        raise ValueError("z_threshold must be positive")
    if min_cohort_size < 2:
        raise ValueError("min_cohort_size must be >= 2")

    by_generation: dict[int, list[LineageEvent]] = {}
    for event in lineage_events:
        by_generation.setdefault(event.generation, []).append(event)

    innovations: list[InnovationEvent] = []
    for generation, cohort in sorted(by_generation.items()):
        if len(cohort) < min_cohort_size:
            continue
        vectors = np.stack([LearningStrategy(*e.learning_strategy).as_vector() for e in cohort])
        mean = vectors.mean(axis=0)
        pooled_std = float(np.linalg.norm(vectors.std(axis=0)))
        if pooled_std <= 0.0:
            continue
        for event, vector in zip(cohort, vectors, strict=True):
            z_score = float(np.linalg.norm(vector - mean)) / pooled_std
            if z_score < z_threshold:
                continue
            persistence = (
                event.death_generation - event.generation
                if event.death_generation is not None
                else None
            )
            innovations.append(
                InnovationEvent(
                    event_id=f"innovation::{event.individual_id}",
                    generation=generation,
                    lineage=event.individual_id,
                    behavior_descriptor=event.learning_strategy,
                    novelty_score=z_score,
                    persistence_duration=persistence,
                    descendant_count=_descendant_count(tracker, event.individual_id),
                )
            )
    innovations.sort(key=lambda e: e.generation)
    return innovations


__all__ = ["InnovationEvent", "detect_innovation_events"]
