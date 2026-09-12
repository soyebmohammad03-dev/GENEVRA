"""Phase 12.5: a GENEVRA-specific evolutionary-activity analysis, built
directly on lineage/strategy machinery GENEVRA already has
(`genevra.analysis.strategy_clustering`) rather than a new persistence
data model.

Every "persistence" measurement here has an explicit, documented
definition (Phase 12.5's requirement) and is computed over *however many
generations the run actually reached* — a run that ends early (extinction,
a budget) is measured over its own actual length, never padded or
extrapolated to a nominal generation count.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any

import numpy as np

from genevra.analysis.stagnation import _trend_slope
from genevra.analysis.strategy_clustering import (
    KMeansClusterer,
    StrategyLineageSummary,
    strategy_lineage_survival,
    strategy_turnover,
)
from genevra.evolution.lineage import LineageEvent

_DEFINITIONS = {
    "lineage_persistence": "fraction of distinct founding lineages (root ancestors present at "
    "generation 0) with at least one living descendant at the final observed generation",
    "strategy_persistence": "per strategy-cluster (see genevra.analysis.strategy_clustering) "
    "fraction of members whose reproduced flag is set — StrategyLineageSummary.persistence",
    "strategy_turnover": "per consecutive generation pair, 1 - (share of the next generation's "
    "birth cohort still in the previous generation's dominant strategy cluster) — "
    "genevra.analysis.strategy_clustering.strategy_turnover",
    "activity_growth_decay": "least-squares slope of behavioral_diversity against generation "
    "index over the whole observed trajectory (genevra.analysis.stagnation._trend_slope)",
}


@dataclass(frozen=True)
class EvolutionaryActivityReport:
    n_generations_observed: int
    lineage_persistence: float
    strategy_summaries: tuple[StrategyLineageSummary, ...]
    strategy_turnover_series: tuple[float, ...]
    diversity_growth_decay_slope: float
    definitions: dict[str, str] = field(default_factory=lambda: dict(_DEFINITIONS))
    note: str = (
        "Persistence/turnover here describe this run's own lineage and strategy-cluster "
        "records only, over however many generations it actually reached. A high "
        "lineage_persistence does not imply the surviving lineages are adaptively "
        "superior, only that they have living descendants at the final observed "
        "generation."
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "n_generations_observed": self.n_generations_observed,
            "lineage_persistence": self.lineage_persistence,
            "strategy_summaries": [
                {
                    "cluster_id": s.cluster_id,
                    "num_individuals": s.num_individuals,
                    "persistence": s.persistence,
                    "generation_span": list(s.generation_span),
                }
                for s in self.strategy_summaries
            ],
            "strategy_turnover_series": list(self.strategy_turnover_series),
            "diversity_growth_decay_slope": self.diversity_growth_decay_slope,
            "definitions": self.definitions,
            "note": self.note,
        }


def _lineage_persistence(lineage_events: Sequence[LineageEvent], final_generation: int) -> float:
    """Founders (`parent_ids == ()`) are the roots; a founder "persists"
    if it, or any of its transitive descendants, has no `death_generation`
    recorded by `final_generation` (i.e. was alive at the run's end)."""
    by_id = {e.individual_id: e for e in lineage_events}
    founders = [e for e in lineage_events if not e.parent_ids]
    if not founders:
        return 0.0

    children_of: dict[int, list[int]] = {}
    for event in lineage_events:
        for parent in event.parent_ids:
            children_of.setdefault(parent, []).append(event.individual_id)

    def _has_living_descendant(root_id: int) -> bool:
        frontier = [root_id]
        seen: set[int] = set()
        while frontier:
            current = frontier.pop()
            event = by_id.get(current)
            if event is not None and (
                event.death_generation is None or event.death_generation > final_generation
            ):
                return True
            for child in children_of.get(current, ()):
                if child not in seen:
                    seen.add(child)
                    frontier.append(child)
        return False

    surviving = sum(1 for founder in founders if _has_living_descendant(founder.individual_id))
    return surviving / len(founders)


def build_activity_report(
    trajectory: Sequence[Mapping[str, Any]],
    lineage_events: Sequence[LineageEvent],
    rng: np.random.Generator,
    n_strategy_clusters: int = 3,
) -> EvolutionaryActivityReport:
    if not trajectory:
        raise ValueError("trajectory must be non-empty")
    final_generation = int(trajectory[-1]["generation"])
    behavioral_diversity = [float(g["behavioral_diversity"]) for g in trajectory]

    persistence = _lineage_persistence(lineage_events, final_generation)

    strategy_summaries: tuple[StrategyLineageSummary, ...] = ()
    turnover_series: tuple[float, ...] = ()
    if lineage_events:
        clusterer = KMeansClusterer(k=n_strategy_clusters)
        strategy_summaries = strategy_lineage_survival(lineage_events, clusterer, rng)
        by_generation: dict[int, list[LineageEvent]] = {}
        for event in lineage_events:
            by_generation.setdefault(event.generation, []).append(event)
        ordered_generations = [by_generation[g] for g in sorted(by_generation)]
        turnover_series = tuple(strategy_turnover(ordered_generations, clusterer, rng))

    slope = _trend_slope(behavioral_diversity) if len(behavioral_diversity) >= 2 else 0.0

    return EvolutionaryActivityReport(
        n_generations_observed=len(trajectory),
        lineage_persistence=persistence,
        strategy_summaries=strategy_summaries,
        strategy_turnover_series=turnover_series,
        diversity_growth_decay_slope=slope,
    )


__all__ = ["EvolutionaryActivityReport", "build_activity_report"]
