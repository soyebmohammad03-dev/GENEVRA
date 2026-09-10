"""Phase 8.15: a reproducible report pipeline over stored experiment
results — structured evidence assembly, never automatically-generated
prose claiming a discovery.

`build_research_report` reads a `ComparisonResult` (already validated —
callers should run `genevra.analysis.comparison.validate_comparison`
first and inspect its `errors`/`warnings`) and assembles the sections a
GENEVRA research report needs: the question and hypothesis (supplied by
the caller, since GENEVRA cannot know what a given comparison was
designed to test), the conditions/controls/seeds actually run, the
measured results with uncertainty, and explicit limitations. It never
adds interpretive sentences like "this proves..." or "this confirms..."
— `interpretation` is a free-text field the calling researcher fills in
themselves, not generated here.
"""

from __future__ import annotations

import dataclasses
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from typing import Any

import numpy as np

from genevra.analysis.aggregation import (
    BootstrapCI,
    EffectSizeResult,
    bootstrap_confidence_interval,
    cohens_d,
    final_generation_values,
)
from genevra.analysis.comparison import ComparisonResult, ComparisonValidation, validate_comparison


@dataclass(frozen=True)
class ConditionMetricSummary:
    condition: str
    n_runs: int
    n_failed: int
    final_values: tuple[float, ...]
    bootstrap_ci: BootstrapCI | None


@dataclass(frozen=True)
class PairwiseComparison:
    condition_a: str
    condition_b: str
    effect_size: EffectSizeResult


@dataclass(frozen=True)
class ResearchReport:
    """Every section below is data assembled from the supplied
    `ComparisonResult`, except `question`, `hypothesis`,
    `secondary_factors`, and `interpretation`, which the calling
    researcher supplies directly — this module never invents them."""

    question: str
    hypothesis: str
    conditions: tuple[str, ...]
    seeds: tuple[int, ...]
    metric_name: str
    condition_summaries: tuple[ConditionMetricSummary, ...]
    pairwise_comparisons: tuple[PairwiseComparison, ...]
    validation: ComparisonValidation
    secondary_factors: tuple[str, ...] = ()
    limitations: tuple[str, ...] = (
        "Effect sizes and confidence intervals are computed from whatever seed "
        "count the comparison actually used; small seed counts (a handful) "
        "produce wide, unreliable intervals — check n_runs before trusting a CI.",
        "A GenerationSnapshot metric extracted at the final generation reflects "
        "only that run's endpoint, not its full trajectory.",
        "This report does not, and cannot, establish causation beyond what the "
        "compared conditions actually varied — see validation.warnings/errors "
        "for anything that might confound the comparison.",
    )
    interpretation: str = (
        "Not generated automatically. The researcher reviewing this report is "
        "responsible for interpreting whether the results above support, "
        "contradict, or are inconclusive with respect to the stated hypothesis."
    )

    def to_dict(self) -> dict[str, Any]:
        return dataclasses.asdict(self)


def build_research_report(
    result: ComparisonResult,
    question: str,
    hypothesis: str,
    metric_extractor: Callable[[Mapping[str, Any]], float],
    metric_name: str = "metric",
    secondary_factors: Sequence[str] = (),
    rng: np.random.Generator | None = None,
) -> ResearchReport:
    """`metric_extractor` reads one `GenerationSnapshot`-shaped dict (the
    last generation of a run's trajectory) and returns the scalar metric
    this report compares across conditions — e.g.
    `lambda g: g["fitness_summary"]["mean"]`. `rng`, when given, drives
    `bootstrap_confidence_interval`; when omitted (the default),
    confidence intervals are skipped rather than seeded arbitrarily,
    since an unseeded bootstrap would make this report non-reproducible."""
    validation = validate_comparison(result)

    condition_summaries = []
    per_condition_values: dict[str, list[float]] = {}
    for condition_name, runs in result.conditions.items():
        completed_runs = [r for r in runs if r["status"] != "failed"]
        trajectories = [r["trajectory"] for r in completed_runs]
        values = final_generation_values(trajectories, metric_extractor)
        per_condition_values[condition_name] = values
        ci = (
            bootstrap_confidence_interval(values, rng)
            if rng is not None and len(values) >= 2
            else None
        )
        condition_summaries.append(
            ConditionMetricSummary(
                condition=condition_name,
                n_runs=len(runs),
                n_failed=len(runs) - len(completed_runs),
                final_values=tuple(values),
                bootstrap_ci=ci,
            )
        )

    pairwise: list[PairwiseComparison] = []
    names = list(result.conditions)
    for i, name_a in enumerate(names):
        for name_b in names[i + 1 :]:
            a_values, b_values = per_condition_values[name_a], per_condition_values[name_b]
            if len(a_values) >= 2 and len(b_values) >= 2:
                pairwise.append(
                    PairwiseComparison(
                        condition_a=name_a,
                        condition_b=name_b,
                        effect_size=cohens_d(a_values, b_values),
                    )
                )

    return ResearchReport(
        question=question,
        hypothesis=hypothesis,
        conditions=tuple(result.conditions),
        seeds=result.seeds,
        metric_name=metric_name,
        condition_summaries=tuple(condition_summaries),
        pairwise_comparisons=tuple(pairwise),
        validation=validation,
        secondary_factors=tuple(secondary_factors),
    )
