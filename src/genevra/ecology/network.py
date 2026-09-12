"""Phase 15.7: ecological interaction network analysis.

Wraps `genevra.ecology.interactions.InteractionNetwork` (degree/density/
type-diversity, already computed there) and adds turnover/stability
across two networks from consecutive time windows. Modularity and
nestedness are explicitly NOT computed here: a meaningful implementation
needs a graph library (e.g. `networkx`/`python-louvain`), which is not an
existing GENEVRA dependency, and a hand-rolled version on GENEVRA's small
interaction graphs would be more likely to mislead than inform. See
`docs/ecology.md` for what adding that dependency would require.
"""

from __future__ import annotations

import dataclasses
from dataclasses import dataclass
from typing import Any

from genevra.ecology.interactions import EcologicalInteraction, InteractionNetwork

_MIN_NODES_FOR_STRUCTURE = 6
_MIN_EDGES_FOR_STRUCTURE = 6


@dataclass(frozen=True)
class NetworkAnalysisResult:
    n_nodes: int
    n_edges: int
    degree: dict[int, int]
    density: float | None
    interaction_type_diversity: float
    structure_analysis_available: bool
    """False (with `density=None` too, when density itself was also
    insufficient) whenever the graph is too small for degree/edge-based
    statistics to be meaningful — an explicit insufficient-data state
    (Phase 15.7's requirement) rather than a misleading number computed
    on, e.g., a 2-node graph."""
    insufficient_data_reason: str | None

    def to_dict(self) -> dict[str, Any]:
        return dataclasses.asdict(self)


class EcologicalNetworkAnalyzer:
    def analyze(self, interactions: list[EcologicalInteraction]) -> NetworkAnalysisResult:
        network = InteractionNetwork(interactions=tuple(interactions))
        nodes = network.nodes
        edges = {frozenset((i.actor, i.target)) for i in interactions if i.target is not None}
        if len(nodes) < _MIN_NODES_FOR_STRUCTURE or len(edges) < _MIN_EDGES_FOR_STRUCTURE:
            return NetworkAnalysisResult(
                n_nodes=len(nodes),
                n_edges=len(edges),
                degree={},
                density=None,
                interaction_type_diversity=network.interaction_type_diversity(),
                structure_analysis_available=False,
                insufficient_data_reason=(
                    f"{len(nodes)} node(s) / {len(edges)} edge(s); structure statistics "
                    f"require >= {_MIN_NODES_FOR_STRUCTURE} nodes and "
                    f"{_MIN_EDGES_FOR_STRUCTURE} edges to be meaningful"
                ),
            )
        density = network.density()
        return NetworkAnalysisResult(
            n_nodes=len(nodes),
            n_edges=len(edges),
            degree=network.degree(),
            density=density if isinstance(density, float) else None,
            interaction_type_diversity=network.interaction_type_diversity(),
            structure_analysis_available=True,
            insufficient_data_reason=None,
        )


def interaction_turnover(
    earlier: list[EcologicalInteraction], later: list[EcologicalInteraction]
) -> float | None:
    """Jaccard distance between the sets of (actor, target) edges present
    in two non-overlapping interaction windows: 0.0 = identical edge set,
    1.0 = completely different. `None` if both windows have no edges."""
    edges_a = {(i.actor, i.target) for i in earlier if i.target is not None}
    edges_b = {(i.actor, i.target) for i in later if i.target is not None}
    union = edges_a | edges_b
    if not union:
        return None
    return 1.0 - len(edges_a & edges_b) / len(union)


__all__ = [
    "NetworkAnalysisResult",
    "EcologicalNetworkAnalyzer",
    "interaction_turnover",
]
