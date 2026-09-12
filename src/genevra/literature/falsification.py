"""Phase 11.6: falsification experiment generation — from one observed
association, generate hypotheses (and, via
`genevra.discovery.followup.generate_followup_experiment`, experiment
designs) specifically aimed at disproving it, rather than only ones that
would confirm it.

Reuses `genevra.discovery.hypothesis.Hypothesis` and
`genevra.discovery.followup.ProposedExperiment` instead of introducing a
parallel representation — a falsification hypothesis is still just a
`Hypothesis`, evaluated through the same
`genevra.discovery.loop.evaluate_hypothesis` machinery as any other. This
module never decides which of the generated hypotheses is true; it only
proposes the discriminating experiments a researcher (or the discovery
loop, under an explicit budget) could run.
"""

from __future__ import annotations

from genevra.discovery.followup import ProposedExperiment, generate_followup_experiment
from genevra.discovery.hypothesis import Hypothesis
from genevra.literature.alternative_explanations import standard_alternative_explanations


def generate_falsification_hypotheses(
    independent_variable: str,
    dependent_variable: str,
    observed_direction: str | None = None,
) -> list[Hypothesis]:
    """H1: the claimed mechanism (`independent_variable` itself drives
    `dependent_variable`), plus one competing hypothesis per standard
    confound in `genevra.literature.alternative_explanations` — mirroring
    Phase 11.6's H1-H6 example pattern, generalized to however many
    confounds `standard_alternative_explanations` returns."""
    hypotheses = [
        Hypothesis(
            hypothesis_id=f"falsify::{independent_variable}::{dependent_variable}::mechanism",
            statement=(
                f"{independent_variable} itself contributes to {dependent_variable} "
                "(the claimed mechanism)."
            ),
            independent_variable=independent_variable,
            dependent_variable=dependent_variable,
            predicted_direction=observed_direction,
            supporting_observations=(),
            conflicting_observations=(),
            source_experiment_ids=(),
            evidence_score=0.0,
        )
    ]
    for explanation in standard_alternative_explanations(independent_variable, dependent_variable):
        confound = explanation.explanation_id.split("::")[-1]
        hypotheses.append(
            Hypothesis(
                hypothesis_id=f"falsify::{explanation.explanation_id}",
                statement=explanation.description,
                independent_variable=confound,
                dependent_variable=dependent_variable,
                predicted_direction=None,
                supporting_observations=(),
                conflicting_observations=(),
                source_experiment_ids=(),
                evidence_score=0.0,
            )
        )
    return hypotheses


def generate_falsification_experiments(
    hypotheses: list[Hypothesis],
    sample_size: int = 8,
    generation_budget: int = 100,
    seed_start: int = 10_000,
) -> list[ProposedExperiment]:
    """Thin pass-through to `generate_followup_experiment` per hypothesis
    — no separate experiment-design logic is introduced here, since a
    falsification test and a discovery follow-up test are the same kind
    of controlled comparison."""
    return [
        generate_followup_experiment(
            h, sample_size=sample_size, generation_budget=generation_budget, seed_start=seed_start
        )
        for h in hypotheses
    ]


__all__ = ["generate_falsification_hypotheses", "generate_falsification_experiments"]
