"""Phase 11.3: `LiteratureReproductionRunner` — loads a
`LiteratureExperimentSpec`, runs its control/treatment conditions via the
existing `genevra.analysis.comparison.ComparisonRunner` (never
reimplementing experiment execution), computes the spec's pre-registered
primary metric, and labels the evidence against the spec's pre-registered
`expected_direction`.

Phase 11.4 (avoid circular reasoning): the primary metric, statistical
test, and expected direction all come from the spec, decided before this
runner ever sees a result — this module has no code path that picks a
different metric after observing which one "worked."

Label semantics (never "confirmed"):

- `INVALID_EXPERIMENT`: the comparison itself is unsound (validation
  errors) or too few completed runs remain per condition to compute
  anything.
- `INCONCLUSIVE`: the permutation test does not reject the null at the
  spec's confidence level — evidence of "no distinguishable effect at
  this sample size," not evidence the claim is false.
- `NOT_SUPPORTED`: a statistically detectable difference exists, in the
  predicted direction, but its Cohen's d is negligible (< 0.2) —
  technically directionally consistent, but too small to call support.
- `PARTIALLY_SUPPORTED`: significant, predicted direction, small-to-medium
  effect (0.2 <= |d| < 0.5).
- `SUPPORTED`: significant, predicted direction, medium-or-larger effect
  (|d| >= 0.5).
- `CONTRADICTED`: significant, but in the direction opposite the one the
  claim predicted.
"""

from __future__ import annotations

import math
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

import numpy as np

from genevra.analysis.aggregation import (
    EffectSizeResult,
    PermutationTestResult,
    cohens_d,
    permutation_test,
)
from genevra.analysis.comparison import ComparisonRunner, ComparisonValidation, validate_comparison
from genevra.experiments.config import ExperimentConfig
from genevra.literature.spec import LiteratureExperimentSpec

_SMALL_EFFECT = 0.2
_MEDIUM_EFFECT = 0.5


class ReproductionLabel(StrEnum):
    SUPPORTED = "SUPPORTED"
    PARTIALLY_SUPPORTED = "PARTIALLY_SUPPORTED"
    NOT_SUPPORTED = "NOT_SUPPORTED"
    CONTRADICTED = "CONTRADICTED"
    INCONCLUSIVE = "INCONCLUSIVE"
    INVALID_EXPERIMENT = "INVALID_EXPERIMENT"


def extract_metric(result: Mapping[str, Any], metric_path: str) -> float | None:
    """Walks `metric_path` (dot-separated; a numeric segment indexes a
    list/tuple, anything else indexes a mapping) into the final generation
    of `result["trajectory"]`. Returns `None` for a failed/extinct run, an
    empty trajectory, or a path that does not resolve — a missing
    measurement is reported as missing, never defaulted to a value that
    would silently bias the comparison."""
    if result.get("status") != "completed":
        return None
    trajectory = result.get("trajectory") or []
    if not trajectory:
        return None
    node: Any = trajectory[-1]
    for part in metric_path.split("."):
        if isinstance(node, Mapping):
            if part not in node:
                return None
            node = node[part]
        elif (
            isinstance(node, Sequence) and not isinstance(node, str) and part.lstrip("-").isdigit()
        ):
            index = int(part)
            if index >= len(node) or index < -len(node):
                return None
            node = node[index]
        else:
            return None
    if node is None:
        return None
    try:
        return float(node)
    except (TypeError, ValueError):
        return None


def classify_evidence(
    control_values: Sequence[float],
    treatment_values: Sequence[float],
    expected_direction: str,
    confidence_level: float,
    rng: np.random.Generator,
) -> tuple[ReproductionLabel, PermutationTestResult, EffectSizeResult, str]:
    """The pure classification core of `LiteratureReproductionRunner.run`,
    factored out so the labeling rule can be unit-tested directly against
    synthetic samples without running a simulation. Requires at least 2
    values in each sample (callers with fewer should use
    `ReproductionLabel.INVALID_EXPERIMENT` instead of calling this)."""
    if len(control_values) < 2 or len(treatment_values) < 2:
        raise ValueError("classify_evidence requires at least 2 values in each sample")
    perm = permutation_test(treatment_values, control_values, rng)
    effect = cohens_d(treatment_values, control_values)
    observed_direction = "positive" if perm.observed_difference > 0 else "negative"
    alpha = 1.0 - confidence_level
    significant = perm.p_value < alpha
    direction_matches = observed_direction == expected_direction
    abs_d = abs(effect.cohens_d) if not math.isnan(effect.cohens_d) else 0.0

    if not significant:
        label = ReproductionLabel.INCONCLUSIVE
    elif not direction_matches:
        label = ReproductionLabel.CONTRADICTED
    elif abs_d < _SMALL_EFFECT:
        label = ReproductionLabel.NOT_SUPPORTED
    elif abs_d < _MEDIUM_EFFECT:
        label = ReproductionLabel.PARTIALLY_SUPPORTED
    else:
        label = ReproductionLabel.SUPPORTED
    return label, perm, effect, observed_direction


@dataclass(frozen=True)
class ReproductionResult:
    spec_id: str
    claim_id: str
    label: ReproductionLabel
    control_values: tuple[float, ...]
    treatment_values: tuple[float, ...]
    permutation: PermutationTestResult | None
    effect_size: EffectSizeResult | None
    observed_direction: str | None
    expected_direction: str
    validation: ComparisonValidation
    n_control: int
    n_treatment: int
    interpretation_note: str = field(
        default=(
            "This label describes whether the pre-registered primary metric, under "
            "the tested GENEVRA conditions, moved in the direction the source claim "
            "predicted. It is evidence about GENEVRA's own model under this "
            "specification, not a verdict on the original paper — 'GENEVRA reproduced "
            "the qualitative pattern' is not the same claim as 'GENEVRA reproduced the "
            "original experiment.'"
        )
    )


class LiteratureReproductionRunner:
    def run(
        self,
        spec: LiteratureExperimentSpec,
        conditions: Mapping[str, Callable[[int], ExperimentConfig]],
        rng: np.random.Generator,
        parallel: bool = False,
    ) -> ReproductionResult:
        if spec.control_condition not in conditions or spec.treatment_condition not in conditions:
            raise ValueError(
                "conditions must contain the spec's control_condition and treatment_condition"
            )
        selected = {
            spec.control_condition: conditions[spec.control_condition],
            spec.treatment_condition: conditions[spec.treatment_condition],
        }
        comparison = ComparisonRunner(conditions=selected, seeds=spec.seeds).run(parallel=parallel)
        validation = validate_comparison(comparison)

        control_raw = comparison.conditions[spec.control_condition]
        treatment_raw = comparison.conditions[spec.treatment_condition]
        control_values = tuple(
            v
            for v in (extract_metric(r, spec.primary_metric) for r in control_raw)
            if v is not None and not math.isnan(v)
        )
        treatment_values = tuple(
            v
            for v in (extract_metric(r, spec.primary_metric) for r in treatment_raw)
            if v is not None and not math.isnan(v)
        )

        if not validation.ok() or len(control_values) < 2 or len(treatment_values) < 2:
            return ReproductionResult(
                spec_id=spec.spec_id,
                claim_id=spec.claim_id,
                label=ReproductionLabel.INVALID_EXPERIMENT,
                control_values=control_values,
                treatment_values=treatment_values,
                permutation=None,
                effect_size=None,
                observed_direction=None,
                expected_direction=spec.expected_direction,
                validation=validation,
                n_control=len(control_values),
                n_treatment=len(treatment_values),
            )

        label, perm, effect, observed_direction = classify_evidence(
            control_values, treatment_values, spec.expected_direction, spec.confidence_level, rng
        )
        return ReproductionResult(
            spec_id=spec.spec_id,
            claim_id=spec.claim_id,
            label=label,
            control_values=control_values,
            treatment_values=treatment_values,
            permutation=perm,
            effect_size=effect,
            observed_direction=observed_direction,
            expected_direction=spec.expected_direction,
            validation=validation,
            n_control=len(control_values),
            n_treatment=len(treatment_values),
        )


__all__ = [
    "ReproductionLabel",
    "ReproductionResult",
    "LiteratureReproductionRunner",
    "extract_metric",
    "classify_evidence",
]
