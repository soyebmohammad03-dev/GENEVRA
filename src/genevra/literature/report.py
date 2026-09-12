"""Phase 11.9: the scientific reproduction report.

Mirrors `genevra.discovery.report.DiscoveryReport`'s convention (a
structured dict/text assembly of evidence plus its own limitations, never
a single verdict). The one requirement specific to this report: it must
never let "GENEVRA reproduced the qualitative pattern" read as "GENEVRA
reproduced the original experiment" — `to_text()` states this distinction
explicitly rather than relying on the reader to infer it.
"""

from __future__ import annotations

import dataclasses
from dataclasses import dataclass, field
from typing import Any

from genevra.discovery.hypothesis import Hypothesis
from genevra.literature.alternative_explanations import AlternativeExplanation
from genevra.literature.claims import LiteratureClaim
from genevra.literature.runner import ReproductionResult
from genevra.literature.spec import LiteratureExperimentSpec

_MODEL_DIFFERENCE_NOTE = (
    "GENEVRA's organism/environment/learning model differs from the source paper's in "
    "ways this claim's genevra_mapping and this spec's approximation_notes enumerate. "
    "This report evaluates whether the tested QUALITATIVE PATTERN holds under "
    "GENEVRA's own assumptions and operationalization — it does not, and cannot, "
    "establish that GENEVRA reproduced the original paper's experiment. Those are "
    "different claims; only the first is ever made here."
)


@dataclass(frozen=True)
class ReproductionReport:
    claim: LiteratureClaim
    spec: LiteratureExperimentSpec
    result: ReproductionResult
    alternative_explanations: tuple[AlternativeExplanation, ...] = ()
    falsification_hypotheses: tuple[Hypothesis, ...] = ()
    model_difference_note: str = field(default=_MODEL_DIFFERENCE_NOTE)

    def to_dict(self) -> dict[str, Any]:
        r = self.result
        return {
            "claim": self.claim.to_dict(),
            "spec": self.spec.to_dict(),
            "result": {
                "label": r.label.value,
                "n_control": r.n_control,
                "n_treatment": r.n_treatment,
                "observed_direction": r.observed_direction,
                "expected_direction": r.expected_direction,
                "effect_size_cohens_d": (
                    r.effect_size.cohens_d if r.effect_size is not None else None
                ),
                "p_value": r.permutation.p_value if r.permutation is not None else None,
                "validation_errors": list(r.validation.errors),
                "validation_warnings": list(r.validation.warnings),
                "interpretation_note": r.interpretation_note,
            },
            "alternative_explanations": [e.to_dict() for e in self.alternative_explanations],
            "falsification_hypotheses": [
                dataclasses.asdict(h) for h in self.falsification_hypotheses
            ],
            "model_difference_note": self.model_difference_note,
        }

    def to_text(self) -> str:
        c, s, r = self.claim, self.spec, self.result
        lines = [f"# Literature Reproduction Report: {c.claim_id}", ""]

        lines.append(f"## Original Claim ({c.source_reference}, {c.source_year})")
        lines.append(c.claim_text)
        lines.append("")

        lines.append("## Original Assumptions")
        lines.append(f"- organism_assumptions: {c.organism_assumptions}")
        lines.append(f"- evolutionary_assumptions: {c.evolutionary_assumptions}")
        lines.append(f"- environmental_regime: {c.environmental_regime}")
        lines.append("")

        lines.append("## GENEVRA Interpretation")
        lines.append(c.genevra_mapping)
        lines.append("")

        lines.append("## Differences Between Models")
        lines.append(self.model_difference_note)
        for note in s.approximation_notes:
            lines.append(f"- {note}")
        lines.append("")

        lines.append("## Experimental Design")
        lines.append(
            f"control={s.control_condition!r} treatment={s.treatment_condition!r} "
            f"seeds={len(s.seeds)} generations={s.generations} "
            f"primary_metric={s.primary_metric!r} statistical_test={s.statistical_test!r}"
        )
        lines.append("")

        lines.append("## Results")
        lines.append(f"n_control={r.n_control} n_treatment={r.n_treatment}")
        if r.permutation is not None:
            lines.append(
                f"observed_difference={r.permutation.observed_difference:.4f} "
                f"p_value={r.permutation.p_value:.4f}"
            )
        if r.effect_size is not None:
            lines.append(f"cohens_d={r.effect_size.cohens_d:.4f}")
        lines.append(
            f"observed_direction={r.observed_direction} expected_direction={r.expected_direction}"
        )
        if r.validation.warnings:
            lines.append(f"validation_warnings={list(r.validation.warnings)}")
        lines.append("")

        lines.append(f"## Label: {r.label.value}")
        lines.append(r.interpretation_note)
        lines.append("")

        lines.append("## Alternative Explanations")
        if not self.alternative_explanations:
            lines.append("(none generated for this report)")
        for e in self.alternative_explanations:
            lines.append(
                f"- [{e.status}] {e.description} "
                f"(discriminating experiment: {e.discriminating_experiment})"
            )
        lines.append("")

        lines.append("## Falsification Tests (generated; execution/labeling is separate)")
        if not self.falsification_hypotheses:
            lines.append("(none generated for this report)")
        for h in self.falsification_hypotheses:
            lines.append(f"- {h.statement}")
        lines.append("")

        lines.append("## Replication Status")
        lines.append(c.replication_status)
        lines.append("")

        lines.append("## Limitations")
        for limitation in c.known_limitations:
            lines.append(f"- {limitation}")
        lines.append("")

        lines.append("## Interpretation")
        lines.append(
            "Under the tested GENEVRA conditions, the pre-registered primary metric's "
            f"evidence is labeled {r.label.value}. This describes agreement between "
            "GENEVRA's own model and the claimed qualitative pattern only — it is "
            "'GENEVRA reproduced the qualitative pattern' evidence at most, never "
            "'GENEVRA reproduced the original experiment.'"
        )
        return "\n".join(lines)


def build_reproduction_report(
    claim: LiteratureClaim,
    spec: LiteratureExperimentSpec,
    result: ReproductionResult,
    alternative_explanations: list[AlternativeExplanation] | None = None,
    falsification_hypotheses: list[Hypothesis] | None = None,
) -> ReproductionReport:
    return ReproductionReport(
        claim=claim,
        spec=spec,
        result=result,
        alternative_explanations=tuple(alternative_explanations or ()),
        falsification_hypotheses=tuple(falsification_hypotheses or ()),
    )


__all__ = ["ReproductionReport", "build_reproduction_report"]
