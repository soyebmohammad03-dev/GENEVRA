"""Reproducibility utilities.

GENEVRA experiments must be replayable from a seed. Every stochastic
component (mutation, environment initialization, sensor noise, etc.) should
draw from a `numpy.random.Generator` obtained here rather than from global
random state, so that two runs with the same seed produce identical
trajectories.
"""

from __future__ import annotations

import random

import numpy as np


def seed_everything(seed: int) -> np.random.Generator:
    """Seed stdlib `random` and return a fresh, seeded NumPy `Generator`.

    Stdlib `random` is seeded too because some dependencies may use it
    internally; GENEVRA's own code should use the returned generator.
    """
    random.seed(seed)
    return np.random.default_rng(seed)
