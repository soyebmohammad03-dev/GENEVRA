"""Phase 10.12: assembles a machine-readable (`to_dict`) and human-
readable (`to_text`) discovery report from the outputs of the rest of
this package. Never writes a grand scientific claim — every section is
evidence plus its own limitations, mirroring
`genevra.analysis.open_endedness.OpenEndednessReport`'s "structured dict,
never a verdict" convention.
"""

from __future__ import annotations

import dataclasses
from dataclasses import dataclass, field
from typing import Any

from genevra.discovery.contradiction import Contradiction
from genevra.discovery.followup import ProposedExperiment
from genevra.discovery.hypothesis import Hypothesis
from genevra.discovery.loop import HypothesisEvaluation
from genevra.discovery.phenomena import PhenomenonObservation

_STANDARD_LIMITATIONS = (
    "Phenomena and correlations are observed patterns under this detector's method "
    "and configuration, not proof of an underlying mechanism.",
    "Correlation results do not establish causation; see each hypothesis's "
    "proposed follow-up experiment for what a controlled test would look like.",
    "Hypothesis evaluation labels ('supported'/'contradicted'/'inconclusive'/"
    "'insufficient_evidence') describe agreement with one replication run at one "
    "sample size, not final scientific conclusions.",
    "Multiple-comparisons correction (genevra.discovery.multiple_testing) reduces, "
    "but does not eliminate, the risk of spurious findings when many relationships "
    "are examined.",
)


@dataclass(frozen=True)
class DiscoveryReport:
    observed_phenomena: tuple[PhenomenonObservation, ...]
    candidate_hypotheses: tuple[Hypothesis, ...]
    contradicting_evidence: tuple[Contradiction, ...]
    follow_up_experiments: tuple[ProposedExperiment, ...]
    hypothesis_evaluations: tuple[HypothesisEvaluation, ...]
    limitations: tuple[str, ...] = field(default=_STANDARD_LIMITATIONS)

    def to_dict(self) -> dict[str, Any]:
        return {
            "observed_phenomena": [dataclasses.asdict(o) for o in self.observed_phenomena],
            "candidate_hypotheses": [dataclasses.asdict(h) for h in self.candidate_hypotheses],
            "contradicting_evidence": [dataclasses.asdict(c) for c in self.contradicting_evidence],
            "follow_up_experiments": [dataclasses.asdict(f) for f in self.follow_up_experiments],
            "hypothesis_evaluations": [dataclasses.asdict(e) for e in self.hypothesis_evaluations],
            "limitations": list(self.limitations),
        }

    def to_text(self) -> str:
        lines = ["# GENEVRA Discovery Report", ""]

        lines.append(f"## Observed Phenomena ({len(self.observed_phenomena)})")
        for observation in self.observed_phenomena:
            lines.append(
                f"- [{observation.experiment} seed={observation.seed}] "
                f"{observation.name}: {observation.description}"
            )
        lines.append("")

        lines.append(f"## Candidate Hypotheses ({len(self.candidate_hypotheses)})")
        for hypothesis in self.candidate_hypotheses:
            lines.append(f"- ({hypothesis.evidence_score:.3f}) {hypothesis.statement}")
        lines.append("")

        lines.append(f"## Contradicting Evidence ({len(self.contradicting_evidence)})")
        for contradiction in self.contradicting_evidence:
            lines.append(
                f"- {contradiction.variable_a} vs {contradiction.variable_b}: "
                f"{contradiction.experiment_a} (rho={contradiction.rho_a:.2f}) disagrees "
                f"with {contradiction.experiment_b} (rho={contradiction.rho_b:.2f})"
            )
        lines.append("")

        lines.append(f"## Follow-up Experiments ({len(self.follow_up_experiments)})")
        for proposal in self.follow_up_experiments:
            lines.append(
                f"- [{proposal.hypothesis_id}] {proposal.independent_variable} -> "
                f"{', '.join(proposal.dependent_variables)} "
                f"(n={proposal.sample_size}, generations={proposal.generation_budget})"
            )
        lines.append("")

        lines.append(f"## Replication Status ({len(self.hypothesis_evaluations)})")
        for evaluation in self.hypothesis_evaluations:
            lines.append(f"- {evaluation.hypothesis_id}: {evaluation.label} — {evaluation.reason}")
        lines.append("")

        lines.append("## Limitations")
        for limitation in self.limitations:
            lines.append(f"- {limitation}")

        return "\n".join(lines)


def build_discovery_report(
    observed_phenomena: list[PhenomenonObservation],
    candidate_hypotheses: list[Hypothesis],
    contradicting_evidence: list[Contradiction],
    follow_up_experiments: list[ProposedExperiment],
    hypothesis_evaluations: list[HypothesisEvaluation],
) -> DiscoveryReport:
    return DiscoveryReport(
        observed_phenomena=tuple(observed_phenomena),
        candidate_hypotheses=tuple(candidate_hypotheses),
        contradicting_evidence=tuple(contradicting_evidence),
        follow_up_experiments=tuple(follow_up_experiments),
        hypothesis_evaluations=tuple(hypothesis_evaluations),
    )


__all__ = ["DiscoveryReport", "build_discovery_report"]
