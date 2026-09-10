"""Lifetime adaptation curves (Phase 8.5): distinguishing "competent at
birth" from "competent after learning" using an organism's actual
per-step rewards, not a raw fitness increase.

**A rising per-step reward trend is not automatically "learning."** It
could just as easily reflect the environment itself changing (dynamics),
or an organism wandering into a resource-rich region by chance. This
module only reports what the reward *signal itself* did over an
organism's lifetime — `initial_competence`, `final_competence`, and
`learning_gain` derived purely from `rewards_by_step` windows — it makes
no claim about *why* the signal changed. Attributing a positive
`learning_gain` specifically to lifetime learning state requires a
controlled comparison against a `NoLearning` control run under the same
conditions (see `docs/research_protocol.md`), not this module alone.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from genevra.evolution.lifetime import LifetimeObservations

_LIMITATION_NOTE = (
    "initial_competence/final_competence/learning_gain are computed purely from "
    "the reward signal's own trajectory over this one lifetime. A positive "
    "learning_gain is consistent with lifetime learning but is not proof of it: "
    "environmental change or chance movement can also produce a rising reward "
    "trend. Attributing learning_gain to lifetime learning specifically requires "
    "comparing against a NoLearning control run under matched conditions."
)


@dataclass(frozen=True)
class AdaptationCurve:
    initial_competence: float
    final_competence: float
    learning_gain: float
    steps_survived: int
    window_size: int
    limitation_note: str = _LIMITATION_NOTE


def compute_adaptation_curve(
    observations: LifetimeObservations, window: int = 10
) -> AdaptationCurve:
    """`initial_competence`: mean reward over the first `min(window,
    steps_survived)` steps. `final_competence`: mean reward over the
    last such window. `learning_gain = final_competence -
    initial_competence`. Overlapping windows (a lifetime shorter than
    `2 * window`) are used as-is rather than raising — the two windows
    then partially or fully overlap, which is reported via `window_size`
    (the actual window length used) so callers can judge whether the
    comparison is meaningful for a very short lifetime."""
    if window <= 0:
        raise ValueError("window must be positive")
    rewards = observations.rewards_by_step
    steps = len(rewards)
    if steps == 0:
        return AdaptationCurve(
            initial_competence=0.0,
            final_competence=0.0,
            learning_gain=0.0,
            steps_survived=0,
            window_size=0,
        )
    effective_window = min(window, steps)
    initial = float(np.mean(rewards[:effective_window]))
    final = float(np.mean(rewards[-effective_window:]))
    return AdaptationCurve(
        initial_competence=initial,
        final_competence=final,
        learning_gain=final - initial,
        steps_survived=steps,
        window_size=effective_window,
    )
