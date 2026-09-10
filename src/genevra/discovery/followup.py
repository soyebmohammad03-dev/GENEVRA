"""Phase 10.6: turns one `Hypothesis` into a `ProposedExperiment` — a
fully specified, human-reviewable experiment design. This module never
runs anything itself: it produces a proposal a researcher (or
`genevra.discovery.loop`, gated by an explicit execution budget) can hand
to `genevra.experiments.matrix.build_experiment_matrix` /
`genevra.analysis.comparison.ComparisonRunner`.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from genevra.discovery.hypothesis import Hypothesis


@dataclass(frozen=True)
class ProposedExperiment:
    hypothesis_id: str
    independent_variable: str
    dependent_variables: tuple[str, ...]
    controls: tuple[str, ...]
    conditions: tuple[str, ...]
    seed_policy: str
    sample_size: int
    generation_budget: int
    analysis_plan: str
    expected_outcomes: dict[str, str]
    possible_confounds: tuple[str, ...]
    note: str = field(
        default="A PROPOSED experiment, not an executed one. Requires an explicit "
        "execution budget (see genevra.discovery.loop) before any run happens."
    )

    def validate(self) -> list[str]:
        """Explicit sanity checks on the proposal itself (Phase 10.6's
        "validated configuration") — not a check that the hypothesis is
        correct, only that the proposed experiment is well-formed enough
        to hand to a runner."""
        problems = []
        if self.sample_size < 2:
            problems.append("sample_size must be >= 2 for any seed-level statistic to be defined")
        if self.generation_budget < 1:
            problems.append("generation_budget must be >= 1")
        if len(self.conditions) < 2:
            problems.append("at least two conditions are required for a controlled comparison")
        if not self.dependent_variables:
            problems.append("at least one dependent variable is required")
        return problems


def generate_followup_experiment(
    hypothesis: Hypothesis,
    sample_size: int = 8,
    generation_budget: int = 100,
    seed_start: int = 10_000,
) -> ProposedExperiment:
    """A generic, template-based proposal: vary `independent_variable`
    across a small number of named conditions ("baseline" vs. a
    perturbed condition), hold everything else fixed, and measure
    `dependent_variable` under independent seeds starting at `seed_start`
    — offset well above typical discovery-data seed ranges so a
    follow-up run is never accidentally seeded identically to the run
    that produced the hypothesis (Phase 10.14's discovery/validation
    split)."""
    conditions = (f"baseline_{hypothesis.independent_variable}", "perturbed")
    return ProposedExperiment(
        hypothesis_id=hypothesis.hypothesis_id,
        independent_variable=hypothesis.independent_variable,
        dependent_variables=(hypothesis.dependent_variable,),
        controls=(
            "population size",
            "environment configuration",
            "generation budget",
            "every gene group other than the independent variable",
        ),
        conditions=conditions,
        seed_policy=f"{sample_size} independent seeds starting at {seed_start}, shared across "
        "every condition (see genevra.analysis.comparison.ComparisonRunner)",
        sample_size=sample_size,
        generation_budget=generation_budget,
        analysis_plan=(
            f"Compare {hypothesis.dependent_variable} across conditions using "
            "genevra.analysis.aggregation.permutation_test and cohens_d; validate the "
            "comparison with genevra.analysis.comparison.validate_comparison before "
            "interpreting; evaluate the hypothesis with "
            "genevra.discovery.loop.evaluate_hypothesis."
        ),
        expected_outcomes={
            "supported": f"perturbed condition shows the predicted "
            f"{hypothesis.predicted_direction or 'directional'} change in "
            f"{hypothesis.dependent_variable} with a non-trivial effect size",
            "contradicted": "perturbed condition shows no effect, or the opposite effect",
            "inconclusive": "effect size or seed count too small to distinguish from chance",
        },
        possible_confounds=(
            "environment regime drawn differently across seeds",
            "interaction with other heritable gene groups not held fixed",
            "founder population composition",
        ),
    )


__all__ = ["ProposedExperiment", "generate_followup_experiment"]
