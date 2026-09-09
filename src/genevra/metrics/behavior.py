"""A lightweight, fixed-length behavioral signature derived from raw
lifetime observations.

This is a discretized summary, not a learned embedding: survival duration,
resources gained, net spatial displacement, unique-cell coverage, and the
distribution over actions taken. It is deliberately simple — the point is
to give diversity/novelty/evolvability metrics a shared, swappable
representation to operate on (`FloatArray -> FloatArray` distance), not to
claim this is the best possible behavioral representation. Richer
representations (full trajectory distance, learned embeddings) can replace
this function later without changing any caller, which only depends on its
signature: `LifetimeObservations -> FloatArray` of fixed length.

No feature standardization is applied — the four scalar features and the
six action-fraction features are on different natural scales. Distance
metrics computed directly on this vector are therefore dominated by
whichever raw feature has the largest scale; documented here as a known
limitation rather than silently accepted.
"""

from __future__ import annotations

import numpy as np

from genevra.arrays import FloatArray
from genevra.evolution.lifetime import LifetimeObservations
from genevra.simulation.types import Action

SIGNATURE_LENGTH = 4 + len(Action)


def behavioral_signature(observations: LifetimeObservations) -> FloatArray:
    action_counts = np.zeros(len(Action), dtype=np.float32)
    for action in observations.actions_taken:
        action_counts[int(action)] += 1.0
    total_actions = max(len(observations.actions_taken), 1)
    action_distribution = action_counts / total_actions

    if observations.positions_visited:
        start, end = observations.positions_visited[0], observations.positions_visited[-1]
        displacement = float(np.hypot(end.x - start.x, end.y - start.y))
        coverage = len(set(observations.positions_visited)) / max(observations.steps_survived, 1)
    else:
        displacement = 0.0
        coverage = 0.0

    scalar_features = np.array(
        [
            float(observations.steps_survived),
            observations.total_resource_gained,
            displacement,
            float(coverage),
        ],
        dtype=np.float32,
    )
    signature: FloatArray = np.concatenate([scalar_features, action_distribution])
    return signature
