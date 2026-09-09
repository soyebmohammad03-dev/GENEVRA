"""An organism's short-term internal state.

Private to the organism: the environment never reads or writes it, and it
is not part of `Observation`. Reset at the start of each lifetime, and
distinct from both the genome (heritable, fixed for the lifetime) and
learning state (plastic weights) — this is working memory, not a plastic
weight delta.

The update rule is a fixed exponential moving average, not itself
genome-encoded or learned.
ponytail: a learned/heritable memory update rule is future work — this is
the minimum viable "organism has internal state that persists across
steps" mechanism, not a claim that this is how memory should ultimately
work.
"""

from __future__ import annotations

import numpy as np

from genevra.arrays import FloatArray


class MemorySystem:
    def __init__(self, size: int, decay: float = 0.8) -> None:
        if size <= 0:
            raise ValueError("memory size must be positive")
        if not 0.0 <= decay <= 1.0:
            raise ValueError("decay must be in [0, 1]")
        self._size = size
        self._decay = decay
        self.state: FloatArray = np.zeros(size, dtype=np.float32)

    def reset(self) -> None:
        self.state = np.zeros(self._size, dtype=np.float32)

    def update(self, input_vector: FloatArray) -> None:
        projected = _project(input_vector, self._size)
        self.state = np.tanh(self._decay * self.state + (1.0 - self._decay) * projected).astype(
            np.float32
        )


def _project(vector: FloatArray, size: int) -> FloatArray:
    """Fixed, RNG-free reduction of an arbitrary-length vector to `size`
    elements: split into `size` contiguous chunks and average each."""
    if vector.size == 0:
        return np.zeros(size, dtype=np.float32)
    chunks = np.array_split(vector, size)
    return np.array(
        [float(chunk.mean()) if chunk.size else 0.0 for chunk in chunks], dtype=np.float32
    )
