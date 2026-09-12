"""Phase 15.2: resource niches.

`SharedGridWorld` already has two resource types (A and B, see
`genevra.simulation.shared_grid_world`); this module does not add a third
kind, it measures how organisms actually use the two that exist, from
each agent's own `StepResult.info["resource_type"]` history (Phase 15/16
change: `SharedGridWorld._attempt_eat` now returns which type was eaten).
No resource-use role is hard-coded onto any organism — preference and
specialization are computed from what an agent actually ate.
"""

from __future__ import annotations

import dataclasses
import math
from collections import Counter
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

_RESOURCE_TYPES = ("A", "B")


@dataclass(frozen=True)
class NicheProfile:
    agent_id: int
    n_acquisitions: int
    preference_a: float | None
    """Fraction of this agent's resource acquisitions that were type A.
    `None` if the agent acquired nothing."""
    specialization: float | None
    """`abs(preference_a - 0.5) * 2`, in [0, 1]: 0.0 = used both types
    equally (a generalist by this measure), 1.0 = used only one type.
    `None` if the agent acquired nothing."""
    breadth: float | None
    """Shannon entropy (natural log, normalized to [0, 1] by dividing by
    ln(2) since there are 2 resource types) over the type distribution.
    1.0 = maximal breadth (equal use), 0.0 = single-type use. `None` if
    the agent acquired nothing."""

    def to_dict(self) -> dict[str, Any]:
        return dataclasses.asdict(self)


def compute_niche_profile(agent_id: int, resource_types_consumed: Sequence[str]) -> NicheProfile:
    """`resource_types_consumed`: one entry ("A" or "B") per successful
    EAT action by this agent, in order — e.g. collected from
    `StepResult.info["resource_type"]` across a run, filtering out
    `None` (a failed EAT attempt)."""
    counts = Counter(t for t in resource_types_consumed if t in _RESOURCE_TYPES)
    total = sum(counts.values())
    if total == 0:
        return NicheProfile(agent_id, 0, None, None, None)
    pref_a = counts.get("A", 0) / total
    specialization = abs(pref_a - 0.5) * 2
    if len(counts) < 2:
        breadth = 0.0
    else:
        breadth = -sum(
            (c / total) * math.log(c / total) for c in counts.values() if c > 0
        ) / math.log(2)
    return NicheProfile(agent_id, total, pref_a, specialization, breadth)


@dataclass(frozen=True)
class PopulationNicheSummary:
    n_agents_with_data: int
    mean_specialization: float | None
    mean_breadth: float | None
    niche_overlap: float | None
    """Population-level niche overlap: 1 - mean pairwise |preference_a
    difference| across agents with data, in [0, 1] (1.0 = every agent has
    an identical resource-type preference; 0.0 = maximally divergent
    preferences, e.g. half exclusively-A and half exclusively-B). `None`
    if fewer than 2 agents have acquisition data."""

    def to_dict(self) -> dict[str, Any]:
        return dataclasses.asdict(self)


def summarize_population_niches(profiles: Sequence[NicheProfile]) -> PopulationNicheSummary:
    with_data = [p for p in profiles if p.preference_a is not None]
    if not with_data:
        return PopulationNicheSummary(0, None, None, None)
    specializations = [p.specialization for p in with_data if p.specialization is not None]
    breadths = [p.breadth for p in with_data if p.breadth is not None]
    mean_spec = sum(specializations) / len(specializations) if specializations else None
    mean_breadth = sum(breadths) / len(breadths) if breadths else None
    overlap: float | None = None
    if len(with_data) >= 2:
        prefs = [p.preference_a for p in with_data if p.preference_a is not None]
        diffs = [
            abs(prefs[i] - prefs[j]) for i in range(len(prefs)) for j in range(i + 1, len(prefs))
        ]
        overlap = 1.0 - (sum(diffs) / len(diffs))
    return PopulationNicheSummary(len(with_data), mean_spec, mean_breadth, overlap)


def resource_types_from_step_infos(infos: Sequence[Mapping[str, Any]]) -> list[str]:
    """Extract the non-`None` `"resource_type"` values from a sequence of
    `StepResult.info` mappings for one agent, in order."""
    return [info["resource_type"] for info in infos if info.get("resource_type") is not None]


__all__ = [
    "NicheProfile",
    "PopulationNicheSummary",
    "compute_niche_profile",
    "summarize_population_niches",
    "resource_types_from_step_infos",
]
