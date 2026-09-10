"""Phase 8.9: keeping "good at the task right now" and "good at adapting"
as separate, inspectable measurements rather than folding them into one
arbitrary combined score.

This module does not decide whether a fitness/adaptability trade-off
exists for a given population — it only assembles the four relevant
per-genotype measurements (already computed elsewhere: initial
competence and learning gain from `genevra.metrics.adaptation`,
generalization performance from `EvolutionConfig.eval_environment_config`
runs, and evolvability from `genevra.metrics.evolvability`) into one
record per sampled genotype, so a researcher can plot or correlate them
without GENEVRA silently deciding how to weigh one against another.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class TradeoffSample:
    """One sampled genotype's measurements along four independent axes.
    Any field may be `None` when that measurement wasn't computed for
    this sample (e.g. no `eval_environment_config` was configured, or
    evolvability analysis wasn't run for this genotype) — a missing
    measurement is reported as missing, never defaulted to a value that
    would silently bias a downstream correlation."""

    individual_id: int
    initial_competence: float | None
    learning_gain: float | None
    eval_shift_fitness: float | None
    evolvability_viable_fraction: float | None
    evolvability_mean_behavioral_distance: float | None


def summarize_tradeoff(samples: list[TradeoffSample]) -> dict[str, float | None]:
    """Pairwise Pearson correlations between whichever axes have enough
    non-missing paired observations (>= 3) across `samples` — a
    descriptive summary, not a claim of a true underlying relationship,
    and `None` for any pair without enough data rather than a fabricated
    number."""
    axes = {
        "initial_competence": [s.initial_competence for s in samples],
        "learning_gain": [s.learning_gain for s in samples],
        "eval_shift_fitness": [s.eval_shift_fitness for s in samples],
        "evolvability_viable_fraction": [s.evolvability_viable_fraction for s in samples],
    }
    result: dict[str, float | None] = {}
    names = list(axes)
    for i, name_a in enumerate(names):
        for name_b in names[i + 1 :]:
            pairs = [
                (a, b)
                for a, b in zip(axes[name_a], axes[name_b], strict=True)
                if a is not None and b is not None
            ]
            key = f"{name_a}__vs__{name_b}"
            if len(pairs) < 3:
                result[key] = None
                continue
            a_values, b_values = zip(*pairs, strict=True)
            if np.std(a_values) == 0.0 or np.std(b_values) == 0.0:
                result[key] = None
                continue
            result[key] = float(np.corrcoef(a_values, b_values)[0, 1])
    return result
