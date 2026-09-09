"""A small feed-forward neural controller: observations in, action logits
out. Deliberately tiny (one hidden layer, plain NumPy) so thousands of
organisms fit on a laptop; weights are held as an explicit
`ControllerArchitecture` + flat parameter vector so they can come straight
from a `Genome` and be evolved without any framework-specific parameter
format.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from genevra.arrays import FloatArray
from genevra.organism.genome import ControllerArchitecture


@dataclass(eq=False)
class Controller:
    architecture: ControllerArchitecture
    weight1: FloatArray
    bias1: FloatArray
    weight2: FloatArray
    bias2: FloatArray

    @classmethod
    def from_weights(
        cls, architecture: ControllerArchitecture, flat_weights: FloatArray
    ) -> Controller:
        if flat_weights.shape != (architecture.num_params,):
            raise ValueError(
                f"expected {architecture.num_params} flat weights, got {flat_weights.shape}"
            )
        i, h, o = architecture.input_size, architecture.hidden_size, architecture.output_size
        offset = 0
        weight1 = flat_weights[offset : offset + i * h].reshape(h, i)
        offset += i * h
        bias1 = flat_weights[offset : offset + h]
        offset += h
        weight2 = flat_weights[offset : offset + h * o].reshape(o, h)
        offset += h * o
        bias2 = flat_weights[offset : offset + o]
        return cls(architecture, weight1, bias1, weight2, bias2)

    def hidden(self, x: FloatArray) -> FloatArray:
        if x.shape != (self.architecture.input_size,):
            raise ValueError(
                f"expected input shape ({self.architecture.input_size},), got {x.shape}"
            )
        activated: FloatArray = (self.weight1 @ x + self.bias1).astype("float32")
        return _tanh(activated)

    def output(
        self, hidden: FloatArray, weights_override: tuple[FloatArray, FloatArray] | None = None
    ) -> FloatArray:
        """Logits for each action.

        `weights_override` lets a `LearningRule` substitute lifetime-
        plastic output weights for the inherited `weight2`/`bias2` without
        the controller needing to know learning exists (see
        `genevra.organism.learning`).
        """
        weight2, bias2 = (
            weights_override if weights_override is not None else (self.weight2, self.bias2)
        )
        logits: FloatArray = (weight2 @ hidden + bias2).astype("float32")
        return logits


def _tanh(x: FloatArray) -> FloatArray:
    result: FloatArray = np.tanh(x).astype("float32")
    return result
