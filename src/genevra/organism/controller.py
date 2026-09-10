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


def batch_hidden(controllers: list[Controller], inputs: FloatArray) -> FloatArray:
    """Vectorized `hidden()` across N *different* controllers (each with
    its own `weight1`/`bias1` — organisms are not weight-sharing), given
    stacked inputs `(N, input_size)`. Returns `(N, hidden_size)`.

    This batches the forward pass itself, not organisms' learning state:
    each row of the result is exactly what `controllers[i].hidden(inputs[i])`
    would produce alone (see `tests/test_controller.py` for the
    equivalence check) — no state is shared or averaged across organisms.
    Requires every controller to share one `ControllerArchitecture` (the
    common case: one population, one evolved architecture); mixed
    architectures must use the individual `hidden()` path per controller.
    """
    if not controllers:
        return np.zeros((0, 0), dtype=np.float32)
    architecture = controllers[0].architecture
    if inputs.shape != (len(controllers), architecture.input_size):
        raise ValueError(
            f"expected inputs shape ({len(controllers)}, {architecture.input_size}), "
            f"got {inputs.shape}"
        )
    weight1 = np.stack([c.weight1 for c in controllers])  # (N, H, I)
    bias1 = np.stack([c.bias1 for c in controllers])  # (N, H)
    activated = np.einsum("nhi,ni->nh", weight1, inputs) + bias1
    result: FloatArray = np.tanh(activated).astype("float32")
    return result


def batch_output(
    controllers: list[Controller],
    hidden: FloatArray,
    weight2_override: FloatArray | None = None,
    bias2_override: FloatArray | None = None,
) -> FloatArray:
    """Vectorized `output()` across N controllers given stacked hidden
    activations `(N, hidden_size)`. `weight2_override`/`bias2_override`
    (each stacked `(N, ...)`), when given, substitute per-organism
    lifetime-plastic output weights, mirroring `Controller.output`'s
    `weights_override` — one override array per organism, never one
    shared across the batch.
    """
    if not controllers:
        return np.zeros((0, 0), dtype=np.float32)
    weight2 = (
        weight2_override
        if weight2_override is not None
        else np.stack([c.weight2 for c in controllers])
    )
    bias2 = (
        bias2_override if bias2_override is not None else np.stack([c.bias2 for c in controllers])
    )
    logits = np.einsum("noh,nh->no", weight2, hidden) + bias2
    result: FloatArray = logits.astype("float32")
    return result
