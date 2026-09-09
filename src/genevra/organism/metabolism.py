"""Energy budget and action costs.

Action costs are heritable (`MetabolicParams`, derived from a genome) and
applied here, not hardcoded in the environment — the environment reports
what resources it made available (`StepResult.reward`); what surviving
costs is an organism property, so that future organisms with different
morphologies/metabolisms can face different trade-offs in the same world.
"""

from __future__ import annotations

from dataclasses import dataclass

from genevra.simulation.types import Action


@dataclass(frozen=True)
class MetabolicParams:
    move_cost: float
    stay_cost: float
    eat_cost: float
    base_upkeep: float


class Metabolism:
    """An organism's mutable energy budget for its current lifetime.
    Reset (via a fresh instance) at the start of each lifetime — never
    part of the genome."""

    def __init__(self, params: MetabolicParams, initial_energy: float) -> None:
        self.params = params
        self.energy = initial_energy

    def cost_for(self, action: Action) -> float:
        if action is Action.EAT:
            return self.params.eat_cost
        if action is Action.STAY:
            return self.params.stay_cost
        return self.params.move_cost

    def apply_step(self, action: Action, resource_gained: float) -> None:
        self.energy -= self.cost_for(action) + self.params.base_upkeep
        self.energy += resource_gained

    @property
    def is_alive(self) -> bool:
        return self.energy > 0.0
