"""Lineage-level summaries built from `LineageTracker` records — a
foundation for later family-tree visualization, not the visualization
itself.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass

import numpy as np

from genevra.evolution.lineage import LineageEvent, LineageTracker


@dataclass(frozen=True)
class LineageSummary:
    founder_id: int
    size: int
    max_generation_reached: int
    still_alive: bool
    extinction_generation: int | None


def summarize_lineages(lineage: LineageTracker) -> list[LineageSummary]:
    """Groups every recorded individual by its founding ancestor (the
    root of its parent chain, or itself if it has no parents) and reports
    per-lineage size, generational reach, and extinction status."""
    groups: dict[int, list[LineageEvent]] = defaultdict(list)
    for event in lineage.events():
        ancestors = lineage.ancestors(event.individual_id)
        founder_id = ancestors[-1] if ancestors else event.individual_id
        groups[founder_id].append(event)

    summaries = []
    for founder_id, group in groups.items():
        still_alive = any(event.death_generation is None for event in group)
        extinction_generation = None
        if not still_alive:
            extinction_generation = max(
                event.death_generation for event in group if event.death_generation is not None
            )
        summaries.append(
            LineageSummary(
                founder_id=founder_id,
                size=len(group),
                max_generation_reached=max(event.generation for event in group),
                still_alive=still_alive,
                extinction_generation=extinction_generation,
            )
        )
    return summaries


def dominant_lineage(summaries: list[LineageSummary]) -> LineageSummary | None:
    """The lineage with the most recorded members — a purely descriptive
    "which founder's descendants make up the most of the run" summary,
    not a claim that larger lineages are more evolutionarily successful
    in any deeper sense."""
    if not summaries:
        return None
    return max(summaries, key=lambda summary: summary.size)


def lineage_diversity(summaries: list[LineageSummary]) -> float:
    """Normalized Shannon entropy over lineage sizes, in `[0, 1]`: `0`
    means one lineage accounts for everyone (total dominance), `1` means
    every lineage is equally represented. `0.0` for 0 or 1 lineages."""
    if len(summaries) < 2:
        return 0.0
    sizes = np.array([summary.size for summary in summaries], dtype=np.float64)
    proportions = sizes / sizes.sum()
    entropy = float(-np.sum(proportions * np.log(proportions)))
    max_entropy = float(np.log(len(summaries)))
    return entropy / max_entropy if max_entropy > 0 else 0.0
