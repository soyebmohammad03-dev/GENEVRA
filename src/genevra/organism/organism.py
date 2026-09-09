"""`Organism`: composes genome, phenotype, sensors, memory, a learning
rule, and metabolism into one lifecycle — a coordinator, not a container
for logic that belongs in its components.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from genevra.arrays import FloatArray
from genevra.organism.genome import Genome
from genevra.organism.learning import LearningRule, LearningState
from genevra.organism.memory import MemorySystem
from genevra.organism.metabolism import Metabolism
from genevra.organism.phenotype import Phenotype, develop
from genevra.organism.sensors import SensorSystem
from genevra.simulation.types import Action, Observation


@dataclass(frozen=True)
class OrganismConfig:
    view_radius: int
    memory_size: int
    initial_energy: float
    channels: int = 2  # local-grid feature planes; 3 for SharedGridWorld's dual resource types


class Organism:
    """One digital organism's lifetime. `act()` and `learn_from_feedback()`
    are separate calls because acting (choosing a move) and learning from
    its consequence (the resulting reward) happen at different points in
    an environment step — see `docs/organism.md` for the intended loop.
    """

    def __init__(
        self,
        genome: Genome,
        config: OrganismConfig,
        learning_rule: LearningRule,
        rng: np.random.Generator,
    ) -> None:
        self.genome = genome
        self.phenotype: Phenotype = develop(genome)
        self.sensors = SensorSystem(config.view_radius, config.channels)
        self.memory = MemorySystem(config.memory_size)
        self.metabolism = Metabolism(self.phenotype.metabolic_params, config.initial_energy)
        self.learning_rule = learning_rule
        self._learning_state: LearningState = learning_rule.init_state(genome.architecture)
        self._rng = rng
        self._last_action: Action | None = None
        self._last_hidden: FloatArray | None = None

        expected_input = self.sensors.output_size + config.memory_size
        if genome.architecture.input_size != expected_input:
            raise ValueError(
                f"genome architecture input_size ({genome.architecture.input_size}) must equal "
                f"sensor output_size + memory_size ({expected_input})"
            )

    def act(self, observation: Observation) -> Action:
        sensory = self.sensors.encode(observation, self.metabolism.energy, self._last_action)
        controller_input: FloatArray = np.concatenate([sensory, self.memory.state])
        hidden = self.phenotype.controller.hidden(controller_input)
        effective_weight2 = self.learning_rule.effective_weights(
            self.phenotype.controller.weight2, self._learning_state
        )
        logits = self.phenotype.controller.output(
            hidden, weights_override=(effective_weight2, self.phenotype.controller.bias2)
        )
        action = _sample_action(logits, self._rng)

        self.memory.update(sensory)
        self._last_hidden = hidden
        self._last_action = action
        return action

    def learn_from_feedback(self, action: Action, resource_gained: float) -> None:
        """Apply this step's metabolic cost/gain and update lifetime
        learning state. Must be called after `act()` returned `action`."""
        if self._last_hidden is None:
            raise RuntimeError("act() must be called before learn_from_feedback()")
        post = _one_hot(action, self.genome.architecture.output_size)
        self._learning_state = self.learning_rule.update(
            self._learning_state,
            pre=self._last_hidden,
            post=post,
            params=self.phenotype.learning_params,
        )
        self.metabolism.apply_step(action, resource_gained)

    @property
    def is_alive(self) -> bool:
        return self.metabolism.is_alive


def _sample_action(logits: FloatArray, rng: np.random.Generator) -> Action:
    shifted = logits - logits.max()
    probs = np.exp(shifted)
    probs = probs / probs.sum()
    index = int(rng.choice(len(probs), p=probs))
    return Action(index)


def _one_hot(action: Action, size: int) -> FloatArray:
    vector: FloatArray = np.zeros(size, dtype=np.float32)
    vector[int(action)] = 1.0
    return vector
