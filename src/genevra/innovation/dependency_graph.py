"""Phase 12.4: `InnovationDependencyGraph` — whether later innovations
depend on earlier ones.

**Never inferred from temporal ordering alone.** An edge `A -> B` is only
added when `B`'s originating individual is an actual genealogical
descendant of `A`'s originating individual (`LineageTracker.ancestors`),
*and* `B` occurred at a later generation. Two innovations that merely
happened one after another, in unrelated lineages, produce no edge. Every
edge still carries `edge_kind="lineage_descent"` and the module-level
`INFERENCE_NOTE` explicitly, because genealogical descent is evidence of
opportunity (B's lineage could inherit whatever A changed), not proof that
A *caused* B to become possible — a true causal claim would need
counterfactual analysis (`genevra.analysis.counterfactual`) this graph
does not perform.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field

from genevra.evolution.lineage import LineageTracker
from genevra.innovation.events import InnovationEvent

INFERENCE_NOTE = (
    "An edge marks that the later innovation's originating individual is a "
    "genealogical descendant of the earlier innovation's originating individual. "
    "This is evidence of opportunity (the later lineage could inherit whatever "
    "changed), not proof of causal dependency — no counterfactual test is performed "
    "here to check whether the later innovation would still have been possible "
    "without the earlier one."
)


@dataclass(frozen=True)
class DependencyEdge:
    source_event_id: str
    target_event_id: str
    edge_kind: str = "lineage_descent"
    note: str = field(default=INFERENCE_NOTE)


@dataclass(frozen=True)
class InnovationDependencyGraph:
    events: tuple[InnovationEvent, ...]
    edges: tuple[DependencyEdge, ...]
    note: str = field(default=INFERENCE_NOTE)

    def descendants_of(self, event_id: str) -> list[str]:
        return [edge.target_event_id for edge in self.edges if edge.source_event_id == event_id]

    def ancestors_of(self, event_id: str) -> list[str]:
        return [edge.source_event_id for edge in self.edges if edge.target_event_id == event_id]


def build_innovation_dependency_graph(
    events: Sequence[InnovationEvent], tracker: LineageTracker
) -> InnovationDependencyGraph:
    """`O(n^2)` in the number of detected innovation events — GENEVRA's
    innovation-event counts are small enough (a filtered z-score outlier
    set, not every birth) for this to stay laptop-feasible without a
    cached ancestor index."""
    ordered = sorted(events, key=lambda e: e.generation)
    edges: list[DependencyEdge] = []
    for later in ordered:
        later_ancestors = set(tracker.ancestors(later.lineage))
        for earlier in ordered:
            if earlier.generation >= later.generation or earlier.event_id == later.event_id:
                continue
            if earlier.lineage in later_ancestors:
                edges.append(
                    DependencyEdge(source_event_id=earlier.event_id, target_event_id=later.event_id)
                )
    return InnovationDependencyGraph(events=tuple(ordered), edges=tuple(edges))


__all__ = [
    "INFERENCE_NOTE",
    "DependencyEdge",
    "InnovationDependencyGraph",
    "build_innovation_dependency_graph",
]
