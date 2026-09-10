"""Phase 10.4/10.5: a structured `Hypothesis` representation, and
deterministic, rule-based generation of candidate hypotheses from
observed patterns. No external LLM is used or required — generation is
template-based over `genevra.discovery.correlation.CorrelationResult` and
`genevra.discovery.phenomena.PhenomenonObservation`, the same structured
evidence a researcher could inspect directly.

Phase 10.8's discovery/prioritization score also lives here: a documented,
interpretable ranking of which candidates deserve investigation first —
never a claim of scientific importance.
"""

from __future__ import annotations

import itertools
from collections.abc import Sequence
from dataclasses import dataclass, field

from genevra.discovery.correlation import CorrelationResult
from genevra.discovery.multiple_testing import FDRResult
from genevra.discovery.phenomena import PhenomenonObservation

_NEVER_TRUTH_NOTE = (
    "A candidate hypothesis, generated from observed patterns in stored experiment "
    "results. It is not established truth: supporting_observations describes what "
    "was consistent with it, conflicting_observations what was not, and "
    "proposed_follow_up_experiment_id (once set) points to the controlled test that "
    "could distinguish it from chance or a confound."
)


@dataclass(frozen=True)
class Hypothesis:
    hypothesis_id: str
    statement: str
    independent_variable: str
    dependent_variable: str
    predicted_direction: str | None
    """`"positive"`, `"negative"`, or `None` when no direction is justified
    by the evidence that generated this hypothesis."""
    supporting_observations: tuple[str, ...]
    conflicting_observations: tuple[str, ...]
    source_experiment_ids: tuple[str, ...]
    evidence_score: float
    proposed_follow_up_experiment_id: str | None = None
    note: str = field(default=_NEVER_TRUTH_NOTE)


def hypotheses_from_correlations(
    correlations: Sequence[CorrelationResult],
    fdr_results: Sequence[FDRResult],
    effect_size_threshold: float = 0.3,
) -> list[Hypothesis]:
    """Template: "If X changes consistently with Y ..., investigate
    whether X predicts Y." One hypothesis per correlation whose FDR-
    corrected result is significant *and* whose effect size clears
    `effect_size_threshold` — a q-value alone does not imply a
    scientifically meaningful effect size, so both are required (Phase
    10.13's "effect-size filtering" approach)."""
    if len(correlations) != len(fdr_results):
        raise ValueError("correlations and fdr_results must be the same length")
    hypotheses = []
    for correlation, fdr in zip(correlations, fdr_results, strict=True):
        if not fdr.significant or abs(correlation.spearman_rho) < effect_size_threshold:
            continue
        direction = "positive" if correlation.spearman_rho > 0 else "negative"
        hypotheses.append(
            Hypothesis(
                hypothesis_id=f"corr::{correlation.variable_a}::{correlation.variable_b}",
                statement=(
                    f"{correlation.variable_a} may be associated with a {direction} change "
                    f"in {correlation.variable_b}; investigate whether "
                    f"{correlation.variable_a} predicts {correlation.variable_b}."
                ),
                independent_variable=correlation.variable_a,
                dependent_variable=correlation.variable_b,
                predicted_direction=direction,
                supporting_observations=(
                    f"spearman_rho={correlation.spearman_rho:.3f}, "
                    f"q_value={fdr.q_value:.4f}, n_runs={correlation.n_runs}, "
                    f"unit_of_analysis={correlation.unit_of_analysis!r}",
                ),
                conflicting_observations=(),
                source_experiment_ids=(),
                evidence_score=abs(correlation.spearman_rho) * (1.0 - fdr.q_value),
            )
        )
    return hypotheses


def hypotheses_from_recurring_phenomena(
    observations: Sequence[PhenomenonObservation], min_seed_count: int = 2
) -> list[Hypothesis]:
    """Template: "If condition A repeatedly produces phenomenon P across
    independent seeds, test whether the pattern persists under further
    independent seeds." Groups observations by `(experiment, phenomenon
    name)`; only phenomena recurring across at least `min_seed_count`
    distinct seeds within the same experiment produce a hypothesis — a
    single-seed observation is not, on its own, evidence of a repeatable
    pattern."""
    by_key: dict[tuple[str, str], list[PhenomenonObservation]] = {}
    for observation in observations:
        by_key.setdefault((observation.experiment, observation.name), []).append(observation)

    hypotheses = []
    for (experiment, phenomenon_name), group in sorted(by_key.items()):
        seeds = {o.seed for o in group}
        if len(seeds) < min_seed_count:
            continue
        hypotheses.append(
            Hypothesis(
                hypothesis_id=f"recur::{experiment}::{phenomenon_name}",
                statement=(
                    f"Phenomenon {phenomenon_name!r} recurred across {len(seeds)} independent "
                    f"seeds in experiment {experiment!r}; test whether it persists under "
                    "further independent seeds."
                ),
                independent_variable="seed",
                dependent_variable=phenomenon_name,
                predicted_direction=None,
                supporting_observations=tuple(o.description for o in group),
                conflicting_observations=(),
                source_experiment_ids=(experiment,),
                evidence_score=min(1.0, len(seeds) / 5.0),
            )
        )
    return hypotheses


@dataclass(frozen=True)
class DiscoveryScoreWeights:
    """Every factor's weight explicit and summed to 1.0 by convention
    (not enforced) so `discovery_score` stays interpretable — change the
    weights to change what "deserves investigation" means, rather than
    editing the scoring formula itself."""

    effect_magnitude: float = 0.35
    reproducibility: float = 0.30
    certainty: float = 0.20
    coverage: float = 0.15


def discovery_score(
    effect_magnitude: float,
    n_independent_seeds: int,
    q_value: float,
    coverage_fraction: float,
    weights: DiscoveryScoreWeights | None = None,
    reproducibility_saturation_seeds: int = 5,
) -> float:
    """A prioritization score in `[0, 1]`, ranking what deserves
    investigation first — never a claim of scientific importance (Phase
    10.8). Computed as a weighted sum of four `[0, 1]`-normalized
    factors:

    - `effect_magnitude`: `min(1, |effect size|)`.
    - `reproducibility`: `min(1, n_independent_seeds / reproducibility_saturation_seeds)`.
    - `certainty`: `1 - q_value` (an FDR-corrected q-value, not a raw p-value).
    - `coverage`: `coverage_fraction` (e.g. fraction of the planned
      experiment matrix already run), supplied by the caller.
    """
    w = weights if weights is not None else DiscoveryScoreWeights()
    reproducibility = min(1.0, n_independent_seeds / reproducibility_saturation_seeds)
    certainty = 1.0 - min(1.0, max(0.0, q_value))
    return float(
        w.effect_magnitude * min(1.0, abs(effect_magnitude))
        + w.reproducibility * reproducibility
        + w.certainty * certainty
        + w.coverage * min(1.0, max(0.0, coverage_fraction))
    )


def rank_hypotheses(hypotheses: Sequence[Hypothesis]) -> list[Hypothesis]:
    """Sorts by `evidence_score` descending — a thin convenience, not a
    second scoring model; `evidence_score` itself is set by whichever
    generation function produced the hypothesis."""
    return sorted(hypotheses, key=lambda h: h.evidence_score, reverse=True)


def deduplicate_hypotheses(hypotheses: Sequence[Hypothesis]) -> list[Hypothesis]:
    seen: set[str] = set()
    result = []
    for hypothesis in hypotheses:
        if hypothesis.hypothesis_id in seen:
            continue
        seen.add(hypothesis.hypothesis_id)
        result.append(hypothesis)
    return result


def _pairwise(iterable: Sequence[str]) -> list[tuple[str, str]]:
    """Convenience for building `variable_pairs` for
    `genevra.discovery.correlation.correlation_discovery` from a flat
    list of variable names."""
    return list(itertools.combinations(iterable, 2))


__all__ = [
    "Hypothesis",
    "hypotheses_from_correlations",
    "hypotheses_from_recurring_phenomena",
    "DiscoveryScoreWeights",
    "discovery_score",
    "rank_hypotheses",
    "deduplicate_hypotheses",
]
