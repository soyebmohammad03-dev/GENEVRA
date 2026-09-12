"""Phase 17.7: a multiple-comparison registry for campaigns with many
hypotheses/metrics. Thin wrapper over the existing
`genevra.discovery.multiple_testing.benjamini_hochberg` — no second
correction procedure is implemented here."""

from __future__ import annotations

import dataclasses
from dataclasses import dataclass
from typing import Any

from genevra.discovery.multiple_testing import benjamini_hochberg


@dataclass(frozen=True)
class ComparisonRecord:
    hypothesis_id: str
    metric: str
    comparison: str
    test: str
    raw_p_value: float
    effect_size: float | None
    is_primary: bool


@dataclass(frozen=True)
class CorrectedComparisonRecord:
    record: ComparisonRecord
    corrected_p_value: float
    significant: bool
    label: str
    """`"confirmatory"` or `"exploratory"` (Phase 17.9), taken directly
    from `record.is_primary` via `benjamini_hochberg`."""

    def to_dict(self) -> dict[str, Any]:
        return {
            **dataclasses.asdict(self.record),
            "corrected_p_value": self.corrected_p_value,
            "significant": self.significant,
            "label": self.label,
        }


def build_multiple_comparison_registry(
    records: list[ComparisonRecord], alpha: float = 0.05
) -> list[CorrectedComparisonRecord]:
    """Corrects every record's p-value together as one family (Phase
    17.7: "record every hypothesis... do not hide non-significant
    results") — never a subset chosen after seeing which ones are
    already significant."""
    if not records:
        return []
    p_values = [r.raw_p_value for r in records]
    is_primary = [r.is_primary for r in records]
    fdr = benjamini_hochberg(p_values, is_primary=is_primary, alpha=alpha)
    return [
        CorrectedComparisonRecord(
            record=record,
            corrected_p_value=result.q_value,
            significant=result.significant,
            label=result.label,
        )
        for record, result in zip(records, fdr, strict=True)
    ]


__all__ = ["ComparisonRecord", "CorrectedComparisonRecord", "build_multiple_comparison_registry"]
