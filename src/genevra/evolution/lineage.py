"""Ancestry tracking: compact per-individual records, not a full object
graph.

Each `LineageEvent` stores an individual's id, parent id(s), birth
generation, a short genome hash (for detecting/comparing genotype changes
across generations without keeping every historical genome around), and
whether/when it died and reproduced. This is the data foundation for later
analysis — family trees, lineage survival/branching, genotype change over
generations — not the analysis itself.
"""

from __future__ import annotations

import dataclasses
import hashlib
from dataclasses import dataclass

from genevra.organism.genome import Genome


@dataclass(eq=False)
class LineageEvent:
    individual_id: int
    parent_ids: tuple[int, ...]
    generation: int
    genome_hash: str
    death_generation: int | None = None
    reproduced: bool = False


class LineageTracker:
    def __init__(self) -> None:
        self._events: dict[int, LineageEvent] = {}

    def record_birth(
        self, individual_id: int, parent_ids: tuple[int, ...], generation: int, genome: Genome
    ) -> None:
        if individual_id in self._events:
            raise ValueError(f"individual {individual_id} already has a birth record")
        self._events[individual_id] = LineageEvent(
            individual_id=individual_id,
            parent_ids=parent_ids,
            generation=generation,
            genome_hash=_hash_genome(genome),
        )

    def record_death(self, individual_id: int, generation: int) -> None:
        self._events[individual_id].death_generation = generation

    def record_reproduction(self, individual_id: int) -> None:
        self._events[individual_id].reproduced = True

    def ancestors(self, individual_id: int) -> list[int]:
        """Parent chain back to a founder. Single-parent in this asexual-
        reproduction model; would branch once recombination exists."""
        chain: list[int] = []
        current = individual_id
        seen: set[int] = set()
        while True:
            event = self._events.get(current)
            if event is None or not event.parent_ids or current in seen:
                break
            seen.add(current)
            parent = event.parent_ids[0]
            chain.append(parent)
            current = parent
        return chain

    def children(self, individual_id: int) -> list[int]:
        return [eid for eid, event in self._events.items() if individual_id in event.parent_ids]

    def events(self) -> list[LineageEvent]:
        """Typed access to the raw records, for analysis code that wants
        to work with real fields rather than re-parsing `to_dicts()`'s
        untyped output."""
        return list(self._events.values())

    def to_dicts(self) -> list[dict[str, object]]:
        return [dataclasses.asdict(event) for event in self._events.values()]

    def __len__(self) -> int:
        return len(self._events)


def _hash_genome(genome: Genome) -> str:
    hasher = hashlib.sha1(usedforsecurity=False)
    for array in (
        genome.controller_weights,
        genome.metabolic_genes,
        genome.mutation_genes,
        genome.learning_genes,
    ):
        hasher.update(array.tobytes())
    return hasher.hexdigest()[:12]
