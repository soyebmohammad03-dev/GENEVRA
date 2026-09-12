"""Phase 12.6: potential vs. realized innovation.

**Potential is not assumed to become realized.** `realized_novelty` is
what the trajectory actually shows (`instantaneous_novelty`, already
computed by `EvolutionEngine`); `mutation_novelty_potential` is what a
mutation-neighborhood sample around sampled genotypes could reach
(`genevra.metrics.evolvability.EvolvabilityAnalyzer`'s
`mean_behavioral_distance`, gathered per generation via
`genevra.analysis.evolvability_over_time.sample_evolvability_over_generations`).
This module only pairs the two series and reports a *descriptive*
agreement measure — sign-of-change agreement, not a correlation p-value —
because per-generation values within one run are autocorrelated, not
independent samples (the same pseudoreplication concern
`genevra.discovery.correlation` documents), and a computed p-value here
would misrepresent that.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Any

from genevra.analysis.evolvability_over_time import EvolvabilitySample

_LIMITATION_NOTE = (
    "Potential (mutation-neighborhood behavioral distance) and realized novelty "
    "(instantaneous_novelty) are paired only at generations both were sampled. No "
    "correlation p-value is computed: per-generation values within one run are "
    "autocorrelated, not independent samples, so a naive p-value would misrepresent "
    "statistical confidence. sign_agreement_fraction is a purely descriptive summary."
)


@dataclass(frozen=True)
class PotentialVsRealizedSample:
    generation: int
    realized_novelty: float
    mutation_novelty_potential: float


@dataclass(frozen=True)
class PotentialVsRealizedReport:
    samples: tuple[PotentialVsRealizedSample, ...]
    realized_minus_potential_mean: float
    """Mean of (realized - potential) across paired generations: positive
    means the population is producing *more* novelty than a single
    mutation step around sampled genotypes alone would predict (e.g. via
    recombination-free but multi-generation drift/selection); negative
    means realized novelty falls short of the sampled mutational
    potential — unrealized potential."""
    sign_agreement_fraction: float | None
    """Fraction of consecutive sampled-generation pairs where realized
    and potential novelty changed in the same direction — `None` when
    fewer than 2 paired samples exist. Descriptive only; see
    `limitation_note`."""
    limitation_note: str = field(default=_LIMITATION_NOTE)

    def to_dict(self) -> dict[str, Any]:
        return {
            "samples": [
                {
                    "generation": s.generation,
                    "realized_novelty": s.realized_novelty,
                    "mutation_novelty_potential": s.mutation_novelty_potential,
                }
                for s in self.samples
            ],
            "realized_minus_potential_mean": self.realized_minus_potential_mean,
            "sign_agreement_fraction": self.sign_agreement_fraction,
            "limitation_note": self.limitation_note,
        }


def build_potential_vs_realized_report(
    evolvability_samples: Sequence[EvolvabilitySample],
    realized_novelty_by_generation: dict[int, float],
) -> PotentialVsRealizedReport:
    """`realized_novelty_by_generation` maps generation -> instantaneous
    novelty (e.g. `{s["generation"]: s["instantaneous_novelty"] for s in
    trajectory}`). When multiple `evolvability_samples` share a
    generation (several genotypes sampled per generation), their
    `mean_behavioral_distance` values are averaged for that generation."""
    by_generation: dict[int, list[float]] = {}
    for sample in evolvability_samples:
        by_generation.setdefault(sample.generation, []).append(
            sample.report.mean_behavioral_distance
        )

    paired: list[PotentialVsRealizedSample] = []
    for generation in sorted(by_generation):
        if generation not in realized_novelty_by_generation:
            continue
        potential = sum(by_generation[generation]) / len(by_generation[generation])
        paired.append(
            PotentialVsRealizedSample(
                generation=generation,
                realized_novelty=realized_novelty_by_generation[generation],
                mutation_novelty_potential=potential,
            )
        )

    if not paired:
        return PotentialVsRealizedReport(
            samples=(), realized_minus_potential_mean=0.0, sign_agreement_fraction=None
        )

    diffs = [s.realized_novelty - s.mutation_novelty_potential for s in paired]
    mean_diff = sum(diffs) / len(diffs)

    sign_agreement: float | None = None
    if len(paired) >= 2:
        agreements = 0
        comparisons = 0
        for previous, current in zip(paired, paired[1:], strict=False):
            realized_delta = current.realized_novelty - previous.realized_novelty
            potential_delta = (
                current.mutation_novelty_potential - previous.mutation_novelty_potential
            )
            if realized_delta == 0.0 or potential_delta == 0.0:
                continue
            comparisons += 1
            if (realized_delta > 0) == (potential_delta > 0):
                agreements += 1
        sign_agreement = agreements / comparisons if comparisons else None

    return PotentialVsRealizedReport(
        samples=tuple(paired),
        realized_minus_potential_mean=mean_diff,
        sign_agreement_fraction=sign_agreement,
    )


__all__ = [
    "PotentialVsRealizedSample",
    "PotentialVsRealizedReport",
    "build_potential_vs_realized_report",
]
