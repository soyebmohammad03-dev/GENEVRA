"""Phase 10.7: the optional research loop — analyze -> detect phenomenon
-> generate hypothesis -> generate a follow-up experiment -> execute if
an explicit budget permits -> evaluate -> label. Every step is an
injected callable/existing module (no reimplementation of experiment
execution here), so this module is pure orchestration plus the labeling
criteria in `evaluate_hypothesis`.

Labels are never "proven": `"supported"`, `"contradicted"`,
`"inconclusive"`, or `"insufficient_evidence"`, each with an explicit,
checkable criterion (see `evaluate_hypothesis`).
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Literal

import numpy as np

from genevra.discovery.hypothesis import Hypothesis
from genevra.discovery.replication import EvidenceSet, ReplicationResult, ReplicationRunner

EvaluationLabel = Literal["supported", "contradicted", "inconclusive", "insufficient_evidence"]


@dataclass(frozen=True)
class HypothesisEvaluation:
    hypothesis_id: str
    label: EvaluationLabel
    reason: str
    replication_result: ReplicationResult | None = None


def evaluate_hypothesis(
    hypothesis: Hypothesis,
    replication_result: ReplicationResult | None,
    min_independent_seeds: int = 3,
) -> HypothesisEvaluation:
    """Explicit criteria, checked in order:

    1. `insufficient_evidence`: no replication evidence yet, or fewer
       than `min_independent_seeds` independent seeds in it.
    2. `supported`: the replication's bootstrap CI excludes zero *and*
       its sign agrees with `hypothesis.predicted_direction` (when one
       was given) or with the original evidence's sign (when it wasn't).
    3. `contradicted`: the CI excludes zero but disagrees in sign.
    4. `inconclusive`: enough seeds were gathered, but the CI still
       includes zero — evidence for *no distinguishable effect at this
       sample size*, not evidence the hypothesis is false."""
    if replication_result is None:
        return HypothesisEvaluation(
            hypothesis_id=hypothesis.hypothesis_id,
            label="insufficient_evidence",
            reason="no replication evidence available yet",
        )
    n_seeds = len(replication_result.replication.seeds)
    if n_seeds < min_independent_seeds:
        return HypothesisEvaluation(
            hypothesis_id=hypothesis.hypothesis_id,
            label="insufficient_evidence",
            reason=f"only {n_seeds} independent seed(s), need >= {min_independent_seeds}",
            replication_result=replication_result,
        )

    ci = replication_result.replication_ci
    excludes_zero = ci.low > 0.0 or ci.high < 0.0
    if not excludes_zero:
        return HypothesisEvaluation(
            hypothesis_id=hypothesis.hypothesis_id,
            label="inconclusive",
            reason=f"replication CI [{ci.low:.4g}, {ci.high:.4g}] includes zero",
            replication_result=replication_result,
        )

    expected_positive = (
        hypothesis.predicted_direction == "positive"
        if hypothesis.predicted_direction is not None
        else replication_result.original_mean > 0
    )
    observed_positive = replication_result.replication_mean > 0
    if observed_positive == expected_positive:
        return HypothesisEvaluation(
            hypothesis_id=hypothesis.hypothesis_id,
            label="supported",
            reason=f"replication CI [{ci.low:.4g}, {ci.high:.4g}] excludes zero, "
            "matching the predicted direction",
            replication_result=replication_result,
        )
    return HypothesisEvaluation(
        hypothesis_id=hypothesis.hypothesis_id,
        label="contradicted",
        reason=f"replication CI [{ci.low:.4g}, {ci.high:.4g}] excludes zero, "
        "but in the opposite direction than predicted",
        replication_result=replication_result,
    )


# Injected per (condition run) -> per-seed dependent-variable values, so
# this module never depends on EvolutionEngine/ExperimentRunner directly.
EvidenceCollector = Callable[[Hypothesis, tuple[int, ...]], tuple[float, ...]]


def run_hypothesis_loop(
    hypotheses: list[Hypothesis],
    collect_original_evidence: EvidenceCollector,
    collect_replication_evidence: EvidenceCollector,
    original_seeds: tuple[int, ...],
    replication_seeds: tuple[int, ...],
    rng: np.random.Generator,
    min_independent_seeds: int = 3,
) -> list[HypothesisEvaluation]:
    """Runs steps 5-8 of Phase 10.7 for each hypothesis: gather original
    and replication evidence via the two injected collectors (typically
    thin wrappers around `genevra.analysis.comparison.ComparisonRunner`
    over a `genevra.discovery.followup.ProposedExperiment`), compare with
    `ReplicationRunner`, and label with `evaluate_hypothesis`. Callers
    control the execution budget entirely through what
    `collect_*_evidence` actually runs (or refuses to run) — this
    function performs no budget enforcement of its own."""
    if set(original_seeds) & set(replication_seeds):
        raise ValueError("original_seeds and replication_seeds must not overlap")

    runner = ReplicationRunner()
    evaluations = []
    for hypothesis in hypotheses:
        original_values = collect_original_evidence(hypothesis, original_seeds)
        replication_values = collect_replication_evidence(hypothesis, replication_seeds)
        replication_result = None
        if len(replication_values) >= 2:
            original = EvidenceSet(seeds=original_seeds, values=original_values, source="original")
            replication = EvidenceSet(
                seeds=replication_seeds, values=replication_values, source="replication"
            )
            replication_result = runner.evaluate(
                hypothesis.hypothesis_id, original, replication, rng
            )
        evaluations.append(
            evaluate_hypothesis(hypothesis, replication_result, min_independent_seeds)
        )
    return evaluations


__all__ = [
    "EvaluationLabel",
    "HypothesisEvaluation",
    "evaluate_hypothesis",
    "EvidenceCollector",
    "run_hypothesis_loop",
]
