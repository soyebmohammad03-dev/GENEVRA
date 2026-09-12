"""Phase 15.3: competition-structure metrics computed from a
`ContinuousEvolutionEngine` run's `history` (`EcologicalSnapshot`s) and
`LineageTracker`.

"Competition regime" (weak/strong/symmetric/asymmetric/resource-limited/
spatial) is not a new engine mechanism — it is which
`SharedGridWorldConfig`/`ContinuousEvolutionConfig` values the caller
chooses (e.g. `resource_a_density` and `max_agents` set competition
strength; `genevra.ecology.spatial` provides the spatial regime). This
module only measures the *outcome* of whatever regime was configured.
"""

from __future__ import annotations

import dataclasses
from collections import Counter
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any

import numpy as np

from genevra.evolution.continuous import EcologicalSnapshot
from genevra.evolution.lineage import LineageEvent


def gini_coefficient(values: Sequence[float]) -> float | None:
    """Standard Gini coefficient (0 = perfect equality, 1 = maximal
    inequality) over a non-negative sample. `None` for fewer than 2
    values or an all-zero sample (undefined/degenerate)."""
    if len(values) < 2:
        return None
    arr = np.sort(np.asarray(values, dtype=np.float64))
    if arr.sum() <= 0:
        return None
    n = len(arr)
    index = np.arange(1, n + 1)
    return float((2 * np.sum(index * arr) / (n * arr.sum())) - (n + 1) / n)


def pielou_evenness(counts: Sequence[int]) -> float | None:
    """Pielou's J = H / ln(S): Shannon entropy of a set of category
    counts (e.g. per-lineage-family population share), normalized by the
    maximum possible entropy for that many categories. 1.0 = perfectly
    even; 0.0 = one category dominates. `None` if fewer than 2 non-zero
    categories."""
    nonzero = [c for c in counts if c > 0]
    if len(nonzero) < 2:
        return None
    total = sum(nonzero)
    shannon = -sum((c / total) * np.log(c / total) for c in nonzero)
    return float(shannon / np.log(len(nonzero)))


def herfindahl_index(counts: Sequence[int]) -> float | None:
    """Herfindahl-Hirschman concentration index: sum(share_i^2), in
    (0, 1]. 1.0 = total concentration (one category), 1/n = perfectly
    even across n categories. `None` if the total is 0."""
    total = sum(counts)
    if total <= 0:
        return None
    return float(sum((c / total) ** 2 for c in counts))


@dataclass(frozen=True)
class CompetitionMetrics:
    population_turnover: float | None
    """(total births + total deaths) / mean population size over the
    observed snapshots. `None` if mean population size is 0."""
    fitness_inequality_gini: float | None
    """Gini coefficient over per-founding-lineage descendant-family size
    — a reproductive-success inequality proxy, not fitness itself.
    GENEVRA's `ContinuousEvolutionEngine` does not track a single scalar
    'fitness' per individual; number of descendants is the closest
    realized-success quantity `LineageTracker` actually records."""
    evenness: float | None
    """Pielou's J over founding-lineage family sizes (descendant counts)
    at the end of the run."""
    concentration_hhi: float | None
    """Herfindahl index over the same family-size distribution."""
    lineage_survival_fraction: float | None
    """Fraction of generation-0 founding lineages with at least one
    living descendant (or that are themselves still alive) at the last
    recorded event. `None` if there were no generation-0 founders."""

    def to_dict(self) -> dict[str, Any]:
        return dataclasses.asdict(self)


def _family_sizes(events: Sequence[LineageEvent]) -> dict[int, int]:
    """Founder id (a generation-0 individual, or the earliest recorded
    ancestor) -> count of individuals descended from it, inclusive."""
    by_id = {e.individual_id: e for e in events}

    def founder_of(individual_id: int) -> int:
        current = individual_id
        seen: set[int] = set()
        while current in by_id and by_id[current].parent_ids and current not in seen:
            seen.add(current)
            current = by_id[current].parent_ids[0]
        return current

    sizes: Counter[int] = Counter()
    for event in events:
        sizes[founder_of(event.individual_id)] += 1
    return dict(sizes)


def compute_competition_metrics(
    history: Sequence[EcologicalSnapshot],
    lineage_events: Sequence[LineageEvent],
) -> CompetitionMetrics:
    if not history:
        return CompetitionMetrics(None, None, None, None, None)

    total_births = sum(s.births_since_last_snapshot for s in history)
    total_deaths = sum(s.deaths_since_last_snapshot for s in history)
    mean_pop = float(np.mean([s.population_size for s in history]))
    turnover = (total_births + total_deaths) / mean_pop if mean_pop > 0 else None

    founders = [e for e in lineage_events if not e.parent_ids]
    survival: float | None = None
    if founders:
        by_id = {e.individual_id: e for e in lineage_events}
        children_of: dict[int, list[int]] = {}
        for e in lineage_events:
            for p in e.parent_ids:
                children_of.setdefault(p, []).append(e.individual_id)

        def has_living_descendant(founder_id: int) -> bool:
            stack = [founder_id]
            seen: set[int] = set()
            while stack:
                current = stack.pop()
                if current in seen:
                    continue
                seen.add(current)
                event = by_id.get(current)
                if event is not None and event.death_generation is None:
                    return True
                stack.extend(children_of.get(current, []))
            return False

        survivors = sum(1 for f in founders if has_living_descendant(f.individual_id))
        survival = survivors / len(founders)

    family_sizes = list(_family_sizes(lineage_events).values())
    evenness = pielou_evenness(family_sizes) if family_sizes else None
    concentration = herfindahl_index(family_sizes) if family_sizes else None

    gini = gini_coefficient(family_sizes) if family_sizes else None

    return CompetitionMetrics(
        population_turnover=turnover,
        fitness_inequality_gini=gini,
        evenness=evenness,
        concentration_hhi=concentration,
        lineage_survival_fraction=survival,
    )


__all__ = [
    "gini_coefficient",
    "pielou_evenness",
    "herfindahl_index",
    "CompetitionMetrics",
    "compute_competition_metrics",
]
