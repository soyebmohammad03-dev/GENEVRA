"""Phase 18.6: boundary-condition search — sweep one GENEVRA-exposed
parameter of a literature case and record where the evidence label
transitions (e.g. SUPPORTED at one value, INCONCLUSIVE or CONTRADICTED at
another). This module does not decide whether a boundary is "meaningful"
— it reports the swept values and the label observed at each, so a
researcher can judge that from real data rather than a hidden threshold.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

import numpy as np

from genevra.literature.claims import LiteratureClaim
from genevra.literature.runner import LiteratureReproductionRunner, ReproductionResult
from genevra.literature.spec import LiteratureExperimentSpec

CaseBuilder = Callable[
    [float], tuple[LiteratureClaim, LiteratureExperimentSpec, dict[str, Callable[[int], Any]]]
]
"""A parametrized case factory, e.g.
`lambda period: case_a_plasticity_evolvability_tradeoff(period=int(period), ...)`."""


@dataclass(frozen=True)
class BoundarySweepPoint:
    parameter_value: float
    result: ReproductionResult

    def to_dict(self) -> dict[str, Any]:
        return {
            "parameter_value": self.parameter_value,
            "label": self.result.label.value,
            "n_control": self.result.n_control,
            "n_treatment": self.result.n_treatment,
            "cohens_d": (
                self.result.effect_size.cohens_d if self.result.effect_size is not None else None
            ),
        }


@dataclass(frozen=True)
class BoundarySweepResult:
    parameter_name: str
    claim_id: str
    points: tuple[BoundarySweepPoint, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "parameter_name": self.parameter_name,
            "claim_id": self.claim_id,
            "points": [p.to_dict() for p in self.points],
        }

    def transitions(self) -> list[tuple[float, float, str, str]]:
        """Consecutive swept points whose label differs, as
        `(value_a, value_b, label_a, label_b)` — the actual boundaries
        found, not a single verdict."""
        out = []
        for a, b in zip(self.points, self.points[1:], strict=False):
            if a.result.label != b.result.label:
                out.append(
                    (
                        a.parameter_value,
                        b.parameter_value,
                        a.result.label.value,
                        b.result.label.value,
                    )
                )
        return out


def run_boundary_sweep(
    parameter_name: str,
    build_case: CaseBuilder,
    parameter_values: list[float],
    rng: np.random.Generator,
    parallel: bool = False,
) -> BoundarySweepResult:
    if len(parameter_values) < 2:
        raise ValueError("a boundary sweep needs at least 2 parameter values")
    runner = LiteratureReproductionRunner()
    points = []
    claim_id = ""
    for value in parameter_values:
        claim, spec, conditions = build_case(value)
        claim_id = claim.claim_id
        result = runner.run(spec, conditions, rng, parallel=parallel)
        points.append(BoundarySweepPoint(parameter_value=value, result=result))
    return BoundarySweepResult(
        parameter_name=parameter_name, claim_id=claim_id, points=tuple(points)
    )


__all__ = [
    "CaseBuilder",
    "BoundarySweepPoint",
    "BoundarySweepResult",
    "run_boundary_sweep",
]
