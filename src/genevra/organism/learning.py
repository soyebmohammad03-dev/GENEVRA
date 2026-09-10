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
    """Heritable control of *how* lifetime learning happens (group (C) in
    this module's docstring). Each field corresponds to an actual
    mechanism in `HebbianLearning`, not an arbitrary extra number:

    - `learning_rate`: scales the magnitude of each step's Hebbian
      update (`HebbianLearning.update`) — how fast the plastic delta
      moves.
    - `plasticity_gate`: in `[0, 1]` (mutation-clipped), scales how much
      of the accumulated plastic delta is actually applied to behavior
      in `effective_weights` — an organism can inherit a nonzero
      learning rate yet evolve to suppress its lifetime effect (gate -> 0),
      making "does this lineage actually use its learning capacity"
      independently evolvable from "how fast would it learn if it did."
    - `decay`: in `[0, 1]` (mutation-clipped), the fraction of the
      accumulated plastic delta forgotten each step before the new
      Hebbian term is added — models bounded working-memory-like
      plasticity (decay > 0) versus permanent lifetime accumulation
      (decay = 0).

    Defaults (`plasticity_gate=1.0`, `decay=0.0`) exactly reproduce the
    original single-gene Hebbian rule, so every pre-existing caller that
    only ever set `learning_rate` is unaffected.
    """

    learning_rate: float
    plasticity_gate: float = 1.0
    decay: float = 0.0


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

    def effective_weights(
        self, base_weight2: FloatArray, state: LearningState, params: LearningParams
    ) -> FloatArray: ...


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

    def effective_weights(
        self, base_weight2: FloatArray, state: LearningState, params: LearningParams
    ) -> FloatArray:
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
        retained = state.output_weight_delta * (1.0 - params.decay)
        delta = retained + params.learning_rate * np.outer(post, pre)
        clipped: FloatArray = np.clip(delta, -self._clip, self._clip).astype(np.float32)
        return LearningState(clipped)

    def effective_weights(
        self, base_weight2: FloatArray, state: LearningState, params: LearningParams
    ) -> FloatArray:
        result: FloatArray = (
            base_weight2 + params.plasticity_gate * state.output_weight_delta
        ).astype(np.float32)
        return result


def _zero_delta(architecture: ControllerArchitecture) -> FloatArray:
    zeros: FloatArray = np.zeros(
        (architecture.output_size, architecture.hidden_size), dtype=np.float32
    )
    return zeros
