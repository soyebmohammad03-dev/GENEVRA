"""Verify the observed seed-zero portability diagnosis and report residual drift."""

import argparse
import json
import math
from pathlib import Path

DECISION_FIELDS = ("fitness", "parents", "rng_before", "rng_after")
RNG_FIELDS = ("rng_before", "rng_after")


def numeric_differences(left, right, path=()):
    """Yield absolute differences, requiring compatible numeric structures."""
    if type(left) is not type(right):
        raise ValueError(f"different types at {path}")
    if isinstance(left, dict):
        if left.keys() != right.keys():
            raise ValueError(f"different fields at {path}")
        for key, value in left.items():
            yield from numeric_differences(value, right[key], (*path, key))
    elif isinstance(left, list):
        if len(left) != len(right):
            raise ValueError(f"different lengths at {path}")
        for index, (x, y) in enumerate(zip(left, right, strict=True)):
            yield from numeric_differences(x, y, (*path, index))
    elif isinstance(left, float):
        if not (math.isfinite(left) and math.isfinite(right)):
            raise ValueError(f"non-finite value at {path}")
        if left != right:
            yield path, abs(left - right)
    elif left != right:
        raise ValueError(f"different discrete values at {path}")


def compare(mac, ubuntu):
    """Check the observed tie mechanism without assigning a scientific tolerance."""
    native = (mac["native"]["selection"], ubuntu["native"]["selection"])
    stable = (mac["stable"]["selection"], ubuntu["stable"]["selection"])
    if any(len(rows) != 15 for rows in (*native, *stable)):
        raise ValueError("incomplete baseline traces")
    first = next(
        (
            (index, x, y)
            for index, (x, y) in enumerate(zip(*native, strict=True))
            if any(x[k] != y[k] for k in DECISION_FIELDS)
        ),
        None,
    )
    if first is None:
        raise ValueError("native decision divergence was not reproduced")
    index, x, y = first
    if x["fitness"] != y["fitness"] or any(x[key] != y[key] for key in RNG_FIELDS):
        raise ValueError("fitness or RNG already differed at first decision divergence")
    a, b = x["native_elites"], y["native_elites"]
    if (
        a == b
        or [x["fitness"][i] for i in a] != [x["fitness"][i] for i in b]
        or x["parents"][: len(a)] != a
        or y["parents"][: len(b)] != b
        or x["parents"][len(a) :] != y["parents"][len(b) :]
    ):
        raise ValueError("native difference is not isolated to equal-fitness elites")
    if any(p[k] != q[k] for p, q in zip(*stable, strict=True) for k in DECISION_FIELDS):
        raise ValueError("stable-sort selection traces differ")
    m, u = (r["stable"]["result"] for r in (mac, ubuntu))
    if m["lineage"] != u["lineage"]:
        raise ValueError("stable-sort lineage differs")
    residual = {}
    for path, delta in numeric_differences(m["trajectory"], u["trajectory"]):
        field = path[1]
        summary = residual.setdefault(field, {"count": 0, "max_abs_difference": 0.0})
        summary["count"] += 1
        summary["max_abs_difference"] = max(summary["max_abs_difference"], delta)
    return {
        "seed": 0,
        "environments": [
            {
                key: r[key]
                for key in ("platform", "python", "numpy", "environment", "rng", "numpy_build")
            }
            for r in (mac, ubuntu)
        ],
        "first_decision_difference_zero_based": index,
        "native_first_difference": {"mac": x, "ubuntu": y},
        "stable_selection_rows_equal": len(stable[0]),
        "stable_lineage_rows_equal": len(m["lineage"]),
        "mean_fitness": {
            policy: [
                r[policy]["result"]["trajectory"][-1]["fitness_summary"]["mean"]
                for r in (mac, ubuntu)
            ]
            for policy in ("native", "stable")
        },
        "stable_continuous_residual": residual,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mac", type=Path)
    parser.add_argument("ubuntu", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    inputs = [json.loads(path.read_text(encoding="utf-8")) for path in (args.mac, args.ubuntu)]
    result = compare(*inputs)
    with args.output.open("x", encoding="utf-8") as handle:
        json.dump(result, handle, indent=2)
        handle.write("\n")
