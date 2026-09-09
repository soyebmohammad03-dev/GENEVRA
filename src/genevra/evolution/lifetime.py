"""Runs one organism through one lifetime in one environment instance, and
records what happened as plain data.

`LifetimeObservations` is the RAW OBSERVATIONS layer: what actually
happened, with no scientific interpretation applied. `genevra.evolution.fitness`
derives a scalar fitness from it; `genevra.metrics.behavior` derives a
behavioral signature from it. Neither of those is baked in here — this
module only produces the observations.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from genevra.organism.genome import Genome
from genevra.organism.learning import LearningRule
from genevra.organism.organism import Organism, OrganismConfig
from genevra.simulation.grid_world import GridWorld, GridWorldConfig
from genevra.simulation.types import Action, Position


@dataclass(frozen=True, eq=False)
class LifetimeObservations:
    """What one organism's lifetime actually produced — raw, uninterpreted."""

    steps_survived: int
    total_resource_gained: float
    final_energy: float
    positions_visited: tuple[Position, ...]
    actions_taken: tuple[Action, ...]
    survived_full_lifetime: bool


@dataclass(frozen=True, eq=False)
class LifetimeRecord:
    """A lifetime's observations tagged with the individual that produced
    them, for population-level bookkeeping."""

    individual_id: int
    observations: LifetimeObservations


def run_single_lifetime(
    genome: Genome,
    environment_config: GridWorldConfig,
    organism_config: OrganismConfig,
    learning_rule: LearningRule,
    env_seed: int,
    organism_seed: int,
    max_steps: int,
) -> LifetimeObservations:
    """One organism, one fresh environment instance, one lifetime.

    Fully determined by `(genome, environment_config, organism_config,
    learning_rule, env_seed, organism_seed, max_steps)` — reused by both
    the population evolution loop (`genevra.evolution.engine`) and
    evolvability analysis (`genevra.metrics.evolvability`), which both
    need "run this genome and tell me what happened" without duplicating
    the loop.
    """
    environment = GridWorld(environment_config)
    observation = environment.reset(seed=env_seed)
    organism = Organism(
        genome, organism_config, learning_rule, np.random.default_rng(organism_seed)
    )

    positions: list[Position] = []
    actions: list[Action] = []
    total_resource_gained = 0.0
    steps_survived = 0

    for _ in range(max_steps):
        if not organism.is_alive:
            break
        action = organism.act(observation)
        result = environment.step(action)
        organism.learn_from_feedback(action, result.reward)

        total_resource_gained += result.reward
        steps_survived += 1
        actions.append(action)
        position = result.info.get("position")
        if isinstance(position, Position):
            positions.append(position)
        observation = result.observation

    return LifetimeObservations(
        steps_survived=steps_survived,
        total_resource_gained=total_resource_gained,
        final_energy=organism.metabolism.energy,
        positions_visited=tuple(positions),
        actions_taken=tuple(actions),
        survived_full_lifetime=steps_survived == max_steps,
    )
