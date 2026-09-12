"""Phase 12.11: research quality gates for research-grade experiments.

Every gate is an explicit, independently toggleable boolean check against
caller-supplied facts about a run — this module never inspects a result
itself to guess whether a gate passes (e.g. it does not "count seeds" from
a directory of files); the caller states the facts
(`QualityGateInputs`) and this module only applies the pass/fail rule,
so which facts matter is always visible and auditable in one place. Gates
are individually configurable (`QualityGateConfig`) precisely so a
scientifically inappropriate requirement (Phase 12.11's stated concern)
can be disabled rather than forcing every experiment through one fixed
checklist.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class QualityGateConfig:
    """`True` means "this gate is enforced." Set a field `False` to
    exempt a category of experiment from that requirement (e.g. an
    exploratory pilot run legitimately has no held-out validation yet)
    rather than failing every gate check on an irrelevant requirement."""

    require_min_seeds: bool = True
    min_seeds: int = 4
    require_predefined_primary_metric: bool = True
    require_predefined_comparison: bool = True
    require_reproducible_seed_sequence: bool = True
    require_successful_completion: bool = True
    require_no_unexplained_missing_data: bool = True
    require_statistical_test: bool = True
    require_effect_size: bool = True
    require_uncertainty_estimate: bool = True
    require_multiple_testing_correction: bool = False
    """`False` by default: only relevant when many comparisons were
    examined at once (see `genevra.discovery.multiple_testing`) — a
    single pre-registered comparison does not need it."""
    require_independent_replication: bool = False
    require_held_out_validation: bool = False
    require_complete_provenance: bool = True


@dataclass(frozen=True)
class QualityGateInputs:
    """Facts about one specific result, supplied by the caller — this
    module computes nothing from raw experiment data itself."""

    n_independent_seeds: int
    primary_metric_predefined: bool
    comparison_predefined: bool
    seed_sequence_reproducible: bool
    run_completed_successfully: bool
    missing_data_explained: bool
    statistical_test_completed: bool
    effect_size_calculated: bool
    uncertainty_calculated: bool
    multiple_testing_correction_applied: bool
    independent_replication_available: bool
    held_out_validation_available: bool
    provenance_complete: bool


@dataclass(frozen=True)
class QualityGateResult:
    passed_gates: tuple[str, ...]
    failed_gates: tuple[str, ...]
    exempted_gates: tuple[str, ...]
    research_ready: bool
    note: str = field(
        default="'research_ready' means every gate enforced by this config passed for "
        "this result's stated inputs — it is a checklist against caller-supplied facts, "
        "not an independent audit of whether those facts are accurate."
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "passed_gates": list(self.passed_gates),
            "failed_gates": list(self.failed_gates),
            "exempted_gates": list(self.exempted_gates),
            "research_ready": self.research_ready,
            "note": self.note,
        }


_GATES: tuple[tuple[str, str, str], ...] = (
    # (config_flag_name, input_check_expression_name, human label)
    ("require_min_seeds", "min_seeds", "sufficient independent seeds"),
    ("require_predefined_primary_metric", "primary_metric_predefined", "predefined primary metric"),
    ("require_predefined_comparison", "comparison_predefined", "predefined comparison"),
    (
        "require_reproducible_seed_sequence",
        "seed_sequence_reproducible",
        "reproducible seed sequence",
    ),
    ("require_successful_completion", "run_completed_successfully", "successful run completion"),
    (
        "require_no_unexplained_missing_data",
        "missing_data_explained",
        "no unexplained missing data",
    ),
    ("require_statistical_test", "statistical_test_completed", "statistical test completed"),
    ("require_effect_size", "effect_size_calculated", "effect size calculated"),
    ("require_uncertainty_estimate", "uncertainty_calculated", "uncertainty calculated"),
    (
        "require_multiple_testing_correction",
        "multiple_testing_correction_applied",
        "multiple-testing correction applied",
    ),
    (
        "require_independent_replication",
        "independent_replication_available",
        "independent replication available",
    ),
    (
        "require_held_out_validation",
        "held_out_validation_available",
        "held-out validation available",
    ),
    ("require_complete_provenance", "provenance_complete", "provenance complete"),
)


def evaluate_quality_gates(
    inputs: QualityGateInputs, config: QualityGateConfig | None = None
) -> QualityGateResult:
    cfg = config if config is not None else QualityGateConfig()
    passed: list[str] = []
    failed: list[str] = []
    exempted: list[str] = []

    for config_flag, input_name, label in _GATES:
        if not getattr(cfg, config_flag):
            exempted.append(label)
            continue
        if input_name == "min_seeds":
            ok = inputs.n_independent_seeds >= cfg.min_seeds
        else:
            ok = bool(getattr(inputs, input_name))
        (passed if ok else failed).append(label)

    return QualityGateResult(
        passed_gates=tuple(passed),
        failed_gates=tuple(failed),
        exempted_gates=tuple(exempted),
        research_ready=not failed,
    )


__all__ = ["QualityGateConfig", "QualityGateInputs", "QualityGateResult", "evaluate_quality_gates"]
