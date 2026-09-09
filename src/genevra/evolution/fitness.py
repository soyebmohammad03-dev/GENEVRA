"""DERIVED FITNESS: a configurable scalar summary of one lifetime's raw
observations.

Deliberately not hardcoded to "food collected" — `LifetimeObservations`
carries several raw signals (survival duration, resources gained, energy
remaining), and `FitnessFunction` is a swappable strategy over them, kept
distinct from the SCIENTIFIC METRICS layer (`genevra.metrics`), which
looks at *populations* of these fitness values (and other signals) over
generations, not at defining what fitness means for one individual.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from genevra.evolution.lifetime import LifetimeObservations


class FitnessFunction(Protocol):
    def compute(self, observations: LifetimeObservations) -> float: ...


@dataclass(frozen=True)
class SurvivalResourceFitness:
    """One reasonable default: a weighted sum of survival duration and
    resources gained. Not a claim that this is "the" correct fitness for
    GENEVRA — swap in a different `FitnessFunction` for a different
    experimental question.
    """

    survival_weight: float = 1.0
    resource_weight: float = 1.0

    def compute(self, observations: LifetimeObservations) -> float:
        return (
            self.survival_weight * observations.steps_survived
            + self.resource_weight * observations.total_resource_gained
        )
