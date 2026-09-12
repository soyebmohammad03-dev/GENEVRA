"""Phase 15.9: data-driven ecological role classification.

Three roles are implemented, each derived from a measured quantity
already produced elsewhere in this codebase — no role is manually
assigned:

- SPECIALIST / GENERALIST: from `NicheProfile.specialization`
  (`genevra.ecology.niches`), thresholded against the *population's own*
  median (data-driven, not a hard-coded absolute cutoff).
- COMPETITOR: from an agent's competition-interaction count relative to
  the population median (`genevra.ecology.interactions`).

EXPLORER, COOPERATIVE_PARTICIPANT, OPPORTUNIST, and STABILIZER are NOT
implemented. COOPERATIVE_PARTICIPANT has no mechanism to measure (see
`genevra.ecology.interactions`). EXPLORER would need a per-agent
behavioral signature computed *during* a `ContinuousEvolutionEngine` run
tied back to agent id — `genevra.metrics.behavior.behavioral_signature`
currently operates on a single-lifetime observation log, not the
continuous per-step stream this engine produces; that instrumentation
does not exist yet. OPPORTUNIST/STABILIZER would need tracking whether
an individual's resource-use or behavior *changes* opportunistically
over its own lifetime, which is not currently recorded per-individual
(only per-lineage learning-strategy-at-birth is). See `docs/ecology.md`.
"""

from __future__ import annotations

import dataclasses
import statistics
from collections import Counter
from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from genevra.ecology.interactions import EcologicalInteraction, InteractionType
from genevra.ecology.niches import NicheProfile


class EcologicalRole(StrEnum):
    SPECIALIST = "specialist"
    GENERALIST = "generalist"
    COMPETITOR = "competitor"
    UNCLASSIFIED = "unclassified"
    """No evidence metric was available for this agent (e.g. it never
    acquired a resource and was never involved in a competition event)."""


@dataclass(frozen=True)
class RoleAssignment:
    agent_id: int
    role: EcologicalRole
    confidence: float
    """In [0, 1]: how far the deciding metric was from the population
    median, normalized by the population's own spread. Not a
    probability — a relative-distinctiveness score."""
    evidence: dict[str, float]

    def to_dict(self) -> dict[str, Any]:
        return dataclasses.asdict(self)


def _median_or_none(values: list[float]) -> float | None:
    return statistics.median(values) if values else None


def classify_roles(
    niche_profiles: Mapping[int, NicheProfile],
    interactions: list[EcologicalInteraction],
) -> list[RoleAssignment]:
    specializations = [
        p.specialization for p in niche_profiles.values() if p.specialization is not None
    ]
    spec_median = _median_or_none(specializations)

    competition_counts: Counter[int] = Counter()
    for interaction in interactions:
        if interaction.interaction_type is InteractionType.COMPETITION:
            competition_counts[interaction.actor] += 1
            if interaction.target is not None:
                competition_counts[interaction.target] += 1
    comp_values = list(competition_counts.values())
    comp_median = _median_or_none([float(v) for v in comp_values]) if comp_values else None

    agent_ids = set(niche_profiles) | set(competition_counts)
    assignments = []
    for agent_id in sorted(agent_ids):
        profile = niche_profiles.get(agent_id)
        n_competitions = float(competition_counts.get(agent_id, 0))
        evidence: dict[str, float] = {"n_competition_events": n_competitions}

        role = EcologicalRole.UNCLASSIFIED
        confidence = 0.0

        if profile is not None and profile.specialization is not None and spec_median is not None:
            evidence["specialization"] = profile.specialization
            spread = max(spec_median, 1e-6)
            if profile.specialization > spec_median:
                role = EcologicalRole.SPECIALIST
                confidence = min(1.0, (profile.specialization - spec_median) / spread)
            elif profile.specialization < spec_median:
                role = EcologicalRole.GENERALIST
                confidence = min(1.0, (spec_median - profile.specialization) / spread)

        if (
            comp_median is not None
            and n_competitions > comp_median
            and n_competitions > (spec_median or 0.0)
        ):
            comp_spread = max(comp_median, 1.0)
            comp_confidence = min(1.0, (n_competitions - comp_median) / comp_spread)
            if role is EcologicalRole.UNCLASSIFIED or comp_confidence > confidence:
                role = EcologicalRole.COMPETITOR
                confidence = comp_confidence

        assignments.append(RoleAssignment(agent_id, role, confidence, evidence))
    return assignments


__all__ = ["EcologicalRole", "RoleAssignment", "classify_roles"]
