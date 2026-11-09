"""Verify and summarize the two-platform metric-reduction traces."""

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path

from compare_baseline_portability import DECISION_FIELDS


def summarize(mac, ubuntu):
    """Check the diagnostic intervention against its native control."""
    runs = (mac, ubuntu)
    rows = [record[mode]["calls"] for record in runs for mode in ("native", "reference")]
    reference = rows[0]
    differences = []
    for i, group in enumerate(zip(*rows, strict=True)):
        vector_size, digest, native_mac, portable = group[0]
        if any(row[:2] != [vector_size, digest] or row[3] != portable for row in group):
            raise ValueError(f"operand or reference norm differs at call {i}")
        if native_mac != group[2][2]:
            differences.append((i, native_mac, group[2][2]))
    trajectories = [
        r[mode]["result"]["trajectory"] for r in runs for mode in ("native", "reference")
    ]
    if not differences or trajectories[0] == trajectories[2] or trajectories[1] != trajectories[3]:
        raise ValueError("intervention did not isolate the native norm differences")
    for field in ("selection", "lineage"):
        values = [
            [tuple(row[key] for key in DECISION_FIELDS) for row in r[mode]["selection"]]
            if field == "selection"
            else r[mode]["result"]["lineage"]
            for r in runs
            for mode in ("native", "reference")
        ]
        if any(value != values[0] for value in values[1:]):
            raise ValueError(f"{field} changed under the intervention")
    first, a, b = differences[0]
    return {
        "norm_calls_per_run": len(reference),
        "operand_lengths": dict(sorted(Counter(row[0] for row in reference).items())),
        "identical_operand_bytes_by_sha256": len(reference),
        "native_norms_different": len(differences),
        "max_absolute_native_norm_difference": max(abs(a - b) for _, a, b in differences),
        "first_difference": {
            "index_zero_based": first,
            "operand_sha256": reference[first][1],
            "mac": a,
            "ubuntu": b,
            "diagnostic_reference": reference[first][3],
        },
        "reference_trajectories_exactly_equal": True,
        "selection_rows_exactly_equal": len(mac["native"]["selection"]),
        "lineage_rows_exactly_equal": len(mac["native"]["result"]["lineage"]),
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mac", type=Path)
    parser.add_argument("ubuntu", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    inputs = [path.read_bytes() for path in (args.mac, args.ubuntu)]
    result = summarize(*(json.loads(data) for data in inputs))
    result["trace_sha256"] = [hashlib.sha256(data).hexdigest() for data in inputs]
    with args.output.open("x", encoding="ascii") as handle:
        json.dump(result, handle, indent=2)
        handle.write("\n")
