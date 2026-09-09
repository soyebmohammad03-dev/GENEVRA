"""Within-lifetime learning, kept structurally separate from evolution.

Three distinct things live here, corresponding to GENEVRA's core research
distinction:

- (A) inherited controller weights — `Controller.weight2`/`bias2`, from
  the genome, untouched by learning.
- (B) lifetime-only plastic state — `LearningState`, created fresh each
  lifetime by `init_state` and discarded when the organism dies; never
  written back into the genome.
- (C) heritable control of *how* learning happens — `LearningParams`
  (currently just a learning rate), derived from `genome.learning_genes`.

`LearningRule` is a swappable strategy so that reinforcement learning,
richer plasticity, or memory-based adaptation can be added later as new
implementations without changing this interface or `Organism`.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

import numpy as np

from genevra.arrays import FloatArray
from genevra.organism.genome import ControllerArchitecture


@dataclass(frozen=True)
class LearningParams:
    learning_rate: float


@dataclass(eq=False)
class LearningState:
    """Lifetime-only plastic delta added on top of the inherited output
    layer. Shape `(output_size, hidden_size)`, matching `Controller.weight2`."""

    output_weight_delta: FloatArray


class LearningRule(Protocol):
    def init_state(self, architecture: ControllerArchitecture) -> LearningState: ...

    def update(
        self, state: LearningState, pre: FloatArray, post: FloatArray, params: LearningParams
    ) -> LearningState: ...

    def effective_weights(self, base_weight2: FloatArray, state: LearningState) -> FloatArray: ...


class NoLearning:
    """The (A)/(B)/(C) split still holds with this rule: state exists and
    is threaded through every call, it simply never changes. Useful as a
    baseline to compare evolved learning against "no lifetime learning"."""

    def init_state(self, architecture: ControllerArchitecture) -> LearningState:
        return LearningState(_zero_delta(architecture))

    def update(
        self, state: LearningState, pre: FloatArray, post: FloatArray, params: LearningParams
    ) -> LearningState:
        return state

    def effective_weights(self, base_weight2: FloatArray, state: LearningState) -> FloatArray:
        return base_weight2


class HebbianLearning:
    """Classic Hebbian update on the output layer only:
    `delta += learning_rate * outer(post, pre)`, clipped to keep the
    plastic component bounded. `learning_rate` comes from `LearningParams`
    (heritable, (C)); `delta` is lifetime state ((B)); `base_weight2`
    stays the untouched inherited weights ((A)).
    """

    def __init__(self, clip: float = 2.0) -> None:
        self._clip = clip

    def init_state(self, architecture: ControllerArchitecture) -> LearningState:
        return LearningState(_zero_delta(architecture))

    def update(
        self, state: LearningState, pre: FloatArray, post: FloatArray, params: LearningParams
    ) -> LearningState:
        delta = state.output_weight_delta + params.learning_rate * np.outer(post, pre)
        clipped: FloatArray = np.clip(delta, -self._clip, self._clip).astype(np.float32)
        return LearningState(clipped)

    def effective_weights(self, base_weight2: FloatArray, state: LearningState) -> FloatArray:
        result: FloatArray = (base_weight2 + state.output_weight_delta).astype(np.float32)
        return result


def _zero_delta(architecture: ControllerArchitecture) -> FloatArray:
    zeros: FloatArray = np.zeros(
        (architecture.output_size, architecture.hidden_size), dtype=np.float32
    )
    return zeros
