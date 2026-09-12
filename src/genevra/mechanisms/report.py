"""A `to_dict()`/`to_text()` report bundling whichever Phase 13 analyses
were actually run for one genome/experiment, following the same
convention as `genevra.discovery.report`, `genevra.literature.report`,
and `genevra.innovation.report`. Every section is optional: a caller
that only ran robustness analysis gets a report with only that section.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from genevra.mechanisms.generalization import GeneralizationProfile
from genevra.mechanisms.mutational_landscape import MutationalLandscapeReport
from genevra.mechanisms.plasticity_cost import PlasticityCostReport
from genevra.mechanisms.robustness import RobustnessProfile


@dataclass(frozen=True)
class MechanismsReport:
    robustness: RobustnessProfile | None = None
    plasticity_cost: PlasticityCostReport | None = None
    generalization: GeneralizationProfile | None = None
    mutational_landscape: MutationalLandscapeReport | None = None
    robustness_evolvability_correlation: float | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "robustness": self.robustness.to_dict() if self.robustness else None,
            "plasticity_cost": self.plasticity_cost.to_dict() if self.plasticity_cost else None,
            "generalization": self.generalization.to_dict() if self.generalization else None,
            "mutational_landscape": (
                self.mutational_landscape.to_dict() if self.mutational_landscape else None
            ),
            "robustness_evolvability_correlation": self.robustness_evolvability_correlation,
        }

    def to_text(self) -> str:
        lines = ["# Evolutionary Mechanisms Report", ""]
        if self.robustness is not None:
            r = self.robustness
            lines.append("## Robustness")
            lines.append(
                f"genetic: mean={r.genetic.mean:.4f} std={r.genetic.std:.4f} "
                f"p10={r.genetic.p10:.4f} (n={r.genetic.n_samples})"
            )
            lines.append(
                f"behavioral: mean={r.behavioral.mean:.4f} std={r.behavioral.std:.4f} "
                f"(n={r.behavioral.n_samples})"
            )
            if r.fitness is not None:
                lines.append(
                    f"fitness |delta|: mean={r.fitness.mean:.4f} (n={r.fitness.n_samples})"
                )
            if r.environmental is not None:
                lines.append(
                    f"environmental |delta|: mean={r.environmental.mean:.4f} "
                    f"(n={r.environmental.n_samples})"
                )
            if r.learning_amplification is not None:
                lines.append(f"learning_amplification={r.learning_amplification:.4f}")
            lines.append("")
        if self.robustness_evolvability_correlation is not None:
            lines.append("## Robustness-Evolvability Association")
            lines.append(
                f"pearson_r={self.robustness_evolvability_correlation:.4f} "
                "(association only; not a causal claim, direction not preselected)"
            )
            lines.append("")
        if self.plasticity_cost is not None:
            lines.append("## Plasticity Cost/Benefit")
            for key, value in self.plasticity_cost.associations.items():
                lines.append(f"{key}: {value if value is not None else 'insufficient data'}")
            lines.append(
                "Note: metabolic energy cost of plasticity is not modeled in GENEVRA's "
                "current organism/metabolism system and is not reported here."
            )
            lines.append("")
        if self.generalization is not None:
            g = self.generalization
            lines.append("## Generalization")
            lines.append(f"train_fitness={g.train.fitness:.4f}")
            for result in g.results:
                retention = g.retention(result.category)
                retention_str = f"{retention:.3f}" if retention is not None else "n/a"
                lines.append(
                    f"{result.category}: fitness={result.fitness:.4f} retention={retention_str} "
                    f"behavioral_distance_from_train={result.behavioral_distance_from_train:.4f}"
                )
            lines.append("")
        if self.mutational_landscape is not None:
            m = self.mutational_landscape.one_step
            lines.append("## Mutational Landscape (one-step)")
            lines.append(
                f"n_samples={m.n_samples} viable_fraction={m.viable_fraction:.3f} "
                f"beneficial_fraction={m.beneficial_fraction} "
                f"deleterious_fraction={m.deleterious_fraction} "
                f"neutral_fraction={m.neutral_fraction}"
            )
            if self.mutational_landscape.two_step is not None:
                t = self.mutational_landscape.two_step
                lines.append(f"two_step: n_samples={t.n_samples} (sampled, not exhaustive)")
            lines.append("")
        lines.append(
            "## Scientific Note\n"
            "Every measurement above is a controlled-perturbation or correlational "
            "measurement of one genotype/population at one point in time. None of it "
            "establishes causation, and no field here should be read as a single "
            "'evolvability' or 'adaptability' score."
        )
        return "\n".join(lines)


__all__ = ["MechanismsReport"]
