"""Phase 17.17: `CampaignReport` — the 22-section scientific campaign
report, following the same `to_dict()`/`to_text()` dataclass convention as
`genevra.literature.report.ReproductionReport` and
`genevra.artifacts.report.ArtifactReportBundle`.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from genevra.campaign.config import CampaignConfig
from genevra.campaign.multiple_comparison import CorrectedComparisonRecord
from genevra.campaign.runner import CampaignRunResult
from genevra.population_analysis.replication_consistency import ReplicationConsistencyReport

_CAUTION_NOTE = (
    "Every effect below is associative unless explicitly stated as a controlled, "
    "predeclared comparison; none establishes a causal mechanism. A CONFIRMATORY label "
    "means the metric/direction/test were predeclared in this campaign's analysis plan "
    "before execution; an EXPLORATORY label means the finding was noticed afterward and "
    "may motivate a future confirmatory campaign, but is not itself confirmation."
)


@dataclass(frozen=True)
class CampaignReport:
    config: CampaignConfig
    run_result: CampaignRunResult
    checkpoint_summary: dict[str, int]
    confirmatory_findings: tuple[CorrectedComparisonRecord, ...] = ()
    exploratory_findings: tuple[CorrectedComparisonRecord, ...] = ()
    replication_consistency: ReplicationConsistencyReport | None = None
    predictive_validation_summary: str = "not evaluated by this campaign"
    figure_names: tuple[str, ...] = ()
    table_names: tuple[str, ...] = ()
    alternative_explanations_summary: str = (
        "see genevra.literature.alternative_explanations for the standard-confound "
        "framework, when this campaign is a literature-reproduction campaign"
    )
    limitations: tuple[str, ...] = ()
    caution_note: str = field(default=_CAUTION_NOTE)

    def to_dict(self) -> dict[str, Any]:
        return {
            "research_question": self.config.research_question,
            "hypotheses": list(self.config.hypotheses),
            "analysis_plan": self.config.analysis_plan.to_dict(),
            "conditions": list(self.config.condition_ids),
            "mode": self.config.mode.value,
            "n_replicates": self.config.n_replicates,
            "campaign_seed": self.config.campaign_seed,
            "population_size": self.config.population_size,
            "generations_or_steps": self.config.generations_or_steps,
            "requested_seeds": self.run_result.requested_seeds,
            "completed_seeds": self.run_result.completed_seeds,
            "failed_seeds": self.run_result.failed_seeds,
            "checkpoint_summary": self.checkpoint_summary,
            "confirmatory_findings": [f.to_dict() for f in self.confirmatory_findings],
            "exploratory_findings": [f.to_dict() for f in self.exploratory_findings],
            "replication_consistency": (
                self.replication_consistency.to_dict() if self.replication_consistency else None
            ),
            "predictive_validation_summary": self.predictive_validation_summary,
            "figures": list(self.figure_names),
            "tables": list(self.table_names),
            "alternative_explanations_summary": self.alternative_explanations_summary,
            "limitations": list(self.limitations),
            "caution_note": self.caution_note,
            "config_hash": self.config.config_hash(),
        }

    def to_text(self) -> str:
        c = self.config
        lines = [f"# Research Campaign Report: {c.campaign_id}", ""]
        lines += ["## 1. Research Question", c.research_question, ""]
        lines += ["## 2. Hypotheses", *[f"- {h}" for h in c.hypotheses], ""]
        plan = c.analysis_plan
        lines += [
            "## 3. Analysis Plan (frozen before execution)",
            f"primary_outcome={plan.primary_outcome!r} "
            f"secondary_outcomes={list(plan.secondary_outcomes)} "
            f"expected_direction={plan.expected_direction!r} comparison={plan.comparison!r} "
            f"test={plan.statistical_test!r} replication_unit={plan.replication_unit!r} "
            f"min_sample_size={plan.min_sample_size}",
            "",
        ]
        lines += [
            "## 4-5. Experimental Design / Conditions",
            f"conditions={list(c.condition_ids)} mode={c.mode.value}",
            "",
        ]
        lines += [
            "## 6. Seed Policy",
            f"campaign_seed={c.campaign_seed} n_replicates={c.n_replicates} "
            "(hierarchical: campaign -> condition -> replicate, "
            "genevra.campaign.seeding)",
            "",
        ]
        lines += [
            "## 7-8. Population / Environment Configuration",
            f"population_size={c.population_size} generations_or_steps={c.generations_or_steps}",
            "",
        ]
        lines += ["## 9-10. Metrics / Statistical Methods", plan.statistical_test, ""]
        lines += [
            "## 11. Results (requested/completed/failed seeds per condition)",
            f"requested={self.run_result.requested_seeds}",
            f"completed={self.run_result.completed_seeds}",
            f"failed={self.run_result.failed_seeds}",
            "",
        ]
        lines += [
            "## 12-13. Effect Sizes / Uncertainty",
            "see confirmatory_findings/exploratory_findings in the JSON report "
            "(effect_size and corrected_p_value per hypothesis)",
            "",
        ]
        lines += [
            "## 14. Replication Consistency",
            (
                f"n_seeds={self.replication_consistency.n_seeds} "
                f"agreement_fraction={self.replication_consistency.agreement_fraction} "
                f"sign_reversals={self.replication_consistency.sign_reversals}"
                if self.replication_consistency
                else "not evaluated by this campaign"
            ),
            "",
        ]
        lines += ["## 15. Predictive Validation", self.predictive_validation_summary, ""]
        lines += [
            "## 16-17. Exploratory / Confirmatory Findings",
            f"n_confirmatory={len(self.confirmatory_findings)} "
            f"n_exploratory={len(self.exploratory_findings)}",
            self.caution_note,
            "",
        ]
        lines += ["## 18. Alternative Explanations", self.alternative_explanations_summary, ""]
        lines += ["## 19. Limitations", *[f"- {lim}" for lim in self.limitations], ""]
        lines += [
            "## 20. Failed / Incomplete Runs",
            f"failed_seeds={self.run_result.failed_seeds}",
            f"checkpoint_summary={self.checkpoint_summary}",
            "",
        ]
        lines += [
            "## 21. Provenance",
            f"config_hash={c.config_hash()} (see manifest.json for git_commit)",
            "",
        ]
        lines += [
            "## 22. Reproducibility Instructions",
            "Re-run with the same campaign_seed and condition factories (checked into "
            "this repository) against a fresh output_root to reproduce every cell; "
            "resuming an interrupted run against the same output_root instead completes "
            "only the pending cells.",
        ]
        return "\n".join(lines)


__all__ = ["CampaignReport"]
