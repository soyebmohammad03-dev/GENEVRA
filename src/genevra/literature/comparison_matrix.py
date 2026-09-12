"""Phase 18.9: the literature comparison matrix — one row per (claim,
GENEVRA result), the exact columns the spec names. Built from
`ReproductionResult`s already produced elsewhere in this module (Phase
11's runner, Phase 18's boundary search); this module does no simulation
of its own, only tabulates existing results, and exports through the
existing `genevra.artifacts.tables` CSV/Markdown helpers rather than a
second table-rendering implementation.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from genevra.artifacts.tables import to_csv, to_markdown
from genevra.literature.claims import LiteratureClaim
from genevra.literature.quality_levels import ReproductionQualityLevel, classify_single_result
from genevra.literature.runner import ReproductionResult

COMPARISON_MATRIX_COLUMNS = (
    "literature_claim",
    "genevra_result",
    "direction",
    "effect_size",
    "confidence",
    "reproduction_level",
    "model_mismatch",
    "status",
)


@dataclass(frozen=True)
class ComparisonRow:
    claim: LiteratureClaim
    result: ReproductionResult

    def to_dict(self) -> dict[str, Any]:
        effect = self.result.effect_size.cohens_d if self.result.effect_size is not None else None
        p_value = self.result.permutation.p_value if self.result.permutation is not None else None
        level = classify_single_result(self.result)
        return {
            "literature_claim": self.claim.claim_id,
            "genevra_result": (
                f"n_control={self.result.n_control} n_treatment={self.result.n_treatment}"
            ),
            "direction": self.result.observed_direction or "n/a",
            "effect_size": f"{effect:.3f}" if effect is not None else "n/a",
            "confidence": f"p={p_value:.4f}" if p_value is not None else "n/a",
            "reproduction_level": level.name,
            "model_mismatch": "; ".join(self.claim.known_limitations) or "none noted",
            "status": self.result.label.value,
        }


def build_comparison_matrix(rows: list[ComparisonRow]) -> list[dict[str, Any]]:
    return [row.to_dict() for row in rows]


def comparison_matrix_csv(rows: list[ComparisonRow]) -> str:
    return to_csv(build_comparison_matrix(rows), COMPARISON_MATRIX_COLUMNS)


def comparison_matrix_markdown(rows: list[ComparisonRow]) -> str:
    return to_markdown(build_comparison_matrix(rows), COMPARISON_MATRIX_COLUMNS)


__all__ = [
    "COMPARISON_MATRIX_COLUMNS",
    "ComparisonRow",
    "build_comparison_matrix",
    "comparison_matrix_csv",
    "comparison_matrix_markdown",
    "ReproductionQualityLevel",
]
