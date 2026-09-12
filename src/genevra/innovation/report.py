"""Phase 12.9: the open-endedness lab report.

Assembles `ExtendedOpenEndednessReport` plus the optional
dependency-graph, potential-vs-realized, and quality-gate sections into
one structured report — mirroring
`genevra.analysis.open_endedness.OpenEndednessReport` and
`genevra.discovery.report.DiscoveryReport`'s "evidence plus limitations,
never a verdict" convention. `to_text()` states explicitly, every time,
that GENEVRA is not being declared "fully open-ended" from this report
(Phase 12.9's explicit requirement).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from genevra.innovation.analyzer import ExtendedOpenEndednessReport
from genevra.innovation.dependency_graph import InnovationDependencyGraph
from genevra.innovation.potential_vs_realized import PotentialVsRealizedReport
from genevra.innovation.quality_gates import QualityGateResult

_NOT_A_VERDICT_NOTE = (
    "GENEVRA is NOT declared 'fully open-ended' by this report merely because some "
    "metrics increase over the observed run. Every section below is a finite-run "
    "proxy for one independent observable, evaluated only against 'no evidence of "
    "saturation within the tested horizon' or similar cautious language — never "
    "against a definition of open-ended evolution this report claims to have solved."
)


@dataclass(frozen=True)
class OpenEndednessLabReport:
    analysis: ExtendedOpenEndednessReport
    dependency_graph: InnovationDependencyGraph | None = None
    potential_vs_realized: PotentialVsRealizedReport | None = None
    quality_gates: QualityGateResult | None = None
    limitations: tuple[str, ...] = (
        "Every trend/shape label describes the observed, finite trajectory only.",
        "Innovation events are detected from heritable learning-strategy outliers, not "
        "from a general definition of behavioral novelty; a genuinely novel behavior "
        "that does not change the learning strategy would not be flagged.",
        "Dependency-graph edges reflect lineage descent, not proven causal dependency.",
        "Potential-vs-realized agreement is descriptive (sign agreement), not an "
        "inferential correlation test, because per-generation values are "
        "autocorrelated.",
    )
    not_a_verdict_note: str = field(default=_NOT_A_VERDICT_NOTE)

    def to_dict(self) -> dict[str, Any]:
        return {
            "analysis": self.analysis.to_dict(),
            "dependency_graph": (
                {
                    "n_events": len(self.dependency_graph.events),
                    "n_edges": len(self.dependency_graph.edges),
                    "edges": [
                        {"source": e.source_event_id, "target": e.target_event_id}
                        for e in self.dependency_graph.edges
                    ],
                    "note": self.dependency_graph.note,
                }
                if self.dependency_graph is not None
                else None
            ),
            "potential_vs_realized": (
                self.potential_vs_realized.to_dict()
                if self.potential_vs_realized is not None
                else None
            ),
            "quality_gates": (
                self.quality_gates.to_dict() if self.quality_gates is not None else None
            ),
            "limitations": list(self.limitations),
            "not_a_verdict_note": self.not_a_verdict_note,
        }

    def to_text(self) -> str:
        lines = ["# GENEVRA Open-Endedness Lab Report", "", self.not_a_verdict_note, ""]

        base = self.analysis.base
        lines.append("## Trajectories")
        for trend in (
            base.novelty_trend,
            base.genotypic_diversity_trend,
            base.behavioral_diversity_trend,
        ):
            direction = "increasing" if trend.increasing else "not increasing"
            lines.append(
                f"- {trend.metric_name}: {direction} (slope={trend.slope:.4g}, "
                f"n={trend.n_generations})"
            )
        if base.evolvability_trend is not None:
            direction = "increasing" if base.evolvability_trend.increasing else "not increasing"
            lines.append(f"- evolvability: {direction} (slope={base.evolvability_trend.slope:.4g})")
        lines.append("")

        if self.analysis.trajectory is not None:
            lines.append("## Trajectory Shapes")
            for summary in self.analysis.trajectory.metric_summaries:
                lines.append(
                    f"- {summary.metric_name}: {summary.shape} — {summary.interpretation_note}"
                )
            lines.append("")

        lines.append("## Innovation Events")
        events = self.analysis.innovation_events or ()
        lines.append(f"({len(events)} detected)")
        for event in events[:20]:
            lines.append(
                f"- gen={event.generation} lineage={event.lineage} "
                f"novelty_score={event.novelty_score:.3f} descendants={event.descendant_count} "
                f"persistence={event.persistence_duration}"
            )
        lines.append("")

        if self.dependency_graph is not None:
            lines.append("## Innovation Dependency Graph (inferred from lineage descent)")
            lines.append(
                f"{len(self.dependency_graph.events)} events, "
                f"{len(self.dependency_graph.edges)} inferred edges"
            )
            lines.append(self.dependency_graph.note)
            lines.append("")

        if self.analysis.activity is not None:
            a = self.analysis.activity
            lines.append("## Evolutionary Activity")
            lines.append(
                f"lineage_persistence={a.lineage_persistence:.3f} "
                f"(over {a.n_generations_observed} observed generations)"
            )
            lines.append(f"diversity_growth_decay_slope={a.diversity_growth_decay_slope:.4g}")
            lines.append("")

        if self.analysis.stagnation is not None:
            s = self.analysis.stagnation
            lines.append("## Stagnation / Recovery")
            lines.append(
                f"stagnation_score={s.stagnation_score:.2f} "
                f"contributing_signals={list(s.contributing_signals)} "
                f"fitness_plateaued={s.fitness_plateaued} (excluded from stagnation_score)"
            )
            lines.append("")

        if self.potential_vs_realized is not None:
            p = self.potential_vs_realized
            lines.append("## Potential vs. Realized Innovation")
            lines.append(
                f"n_paired_samples={len(p.samples)} "
                f"realized_minus_potential_mean={p.realized_minus_potential_mean:.4f} "
                f"sign_agreement_fraction={p.sign_agreement_fraction}"
            )
            lines.append(p.limitation_note)
            lines.append("")

        lines.append("## Environment / Lineage Dependence")
        lines.append(
            "Every measurement above is specific to this run's environment configuration "
            "and lineage history; none is a claim about GENEVRA's behavior under other "
            "configurations without re-running this analysis there."
        )
        lines.append("")

        if self.quality_gates is not None:
            g = self.quality_gates
            lines.append("## Research Quality Gates")
            lines.append(f"research_ready={g.research_ready}")
            lines.append(f"passed={list(g.passed_gates)}")
            lines.append(f"failed={list(g.failed_gates)}")
            lines.append(f"exempted={list(g.exempted_gates)}")
            lines.append("")

        lines.append("## Limitations")
        for limitation in self.limitations:
            lines.append(f"- {limitation}")
        lines.append("")

        lines.append("## Evidence Strength")
        lines.append(self.not_a_verdict_note)
        return "\n".join(lines)


def build_open_endedness_lab_report(
    analysis: ExtendedOpenEndednessReport,
    dependency_graph: InnovationDependencyGraph | None = None,
    potential_vs_realized: PotentialVsRealizedReport | None = None,
    quality_gates: QualityGateResult | None = None,
) -> OpenEndednessLabReport:
    return OpenEndednessLabReport(
        analysis=analysis,
        dependency_graph=dependency_graph,
        potential_vs_realized=potential_vs_realized,
        quality_gates=quality_gates,
    )


__all__ = ["OpenEndednessLabReport", "build_open_endedness_lab_report"]
