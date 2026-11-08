"""Generate analytic power sensitivities and deterministic synthetic design checks."""

import argparse
import json
from pathlib import Path

from genevra.analysis.validation_design import (
    ReferenceStratum,
    adjudicate,
    binomial_lower_tail,
    comparable_package,
    paired_radius,
    passing_count,
    planning_count,
    reference_band,
    risk_upper,
)


def design_receipt() -> dict[str, object]:
    alpha, cap = 0.02, 0.05
    risks = (0.005, 0.01, 0.025, 0.04, 0.05)
    power = []
    for n in (12, 77, 173, 209, 500, 783, 2444):
        cutoff = passing_count(n, cap, alpha)
        power.append(
            {
                "episodes": n,
                "passing_count": cutoff,
                "zero_event_upper": round(risk_upper(0, n, alpha), 9),
                "paired_radius": round(paired_radius(n, alpha), 9),
                "power_by_assumed_adverse_risk": {
                    str(p): round(binomial_lower_tail(cutoff, n, p), 9) if cutoff >= 0 else 0
                    for p in risks
                },
            }
        )
    reachable = ReferenceStratum(90, 90, 9)
    cases = (
        ("covered_channels", (reachable, ReferenceStratum(10, 10, 1)), 0, 0.10),
        ("shared_blindness", (reachable, ReferenceStratum(10, 10, 10)), 0, 0.19),
        ("unsampled_off_channel_stratum", (reachable, ReferenceStratum(10, 0, 0)), 0, 0.19),
        ("off_frame_valid_cap", (reachable,), 0.1, 0.19),
        ("off_frame_invalid_cap", (reachable,), 0.01, 0.19),
        ("unresolved_nonresponse", (ReferenceStratum(100, 100, 10, 10),), 0, 0.20),
    )
    fixtures = []
    for name, strata, off_frame_cap, truth in cases:
        band = reference_band(strata, 0.01, 1, off_frame_cap)
        fixtures.append(
            {
                "case": name,
                "reference": [round(endpoint, 9) for endpoint in band],
                "fixture_truth_in_band": band[0] - 1e-12 <= truth <= band[1] + 1e-12,
                "verdict_for_issued_certificate": adjudicate(band, 0.1, 0.05, True).value,
            }
        )
    return {
        "kind": "analytic planning and deterministic synthetic fixtures; no field observations",
        "safety_alpha": alpha,
        "adverse_risk_cap": cap,
        "power": power,
        "planning_inflation_for_209": [
            {
                "cluster_size": size,
                "icc": icc,
                "loss": loss,
                "nominal_units": planning_count(209, size, icc, loss),
            }
            for size, icc, loss in ((1, 0, 0), (3, 0.05, 0.1), (4, 0.2, 0.2), (6, 0.3, 0.2))
        ],
        "reference_fixtures": fixtures,
        "unequal_cost_comparison_admitted": comparable_package("pkg-a", "pkg-a", 100, 110),
        "unequal_access_comparison_admitted": comparable_package("pkg-a", "pkg-b", 100, 100),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    with args.output.open("x") as stream:
        json.dump(design_receipt(), stream, indent=2, allow_nan=False)
        stream.write("\n")


if __name__ == "__main__":
    main()
