"""Trace stable-baseline vector norms and test a diagnostic reduction reference."""

import argparse
import hashlib
import json
import math
import platform
import sys
from pathlib import Path
from unittest.mock import patch

import numpy as np
from diagnose_baseline_portability import run

from genevra.evolution.engine import EvolutionEngine


def trace(use_reference):
    """Observe original norm inputs and outputs inside the metric snapshot."""
    native_norm = np.linalg.norm
    build_snapshot = EvolutionEngine._build_snapshot
    calls = []

    def norm(vector):
        if vector.ndim != 1 or vector.dtype != np.float32:
            raise ValueError(f"unexpected metric norm operand: {vector.shape}, {vector.dtype}")
        native = float(native_norm(vector))
        reference = float(np.float32(math.sqrt(math.fsum(float(x) ** 2 for x in vector))))
        calls.append(
            [
                vector.size,
                hashlib.sha256(vector.astype("<f4").tobytes()).hexdigest(),
                native,
                reference,
            ]
        )
        return reference if use_reference else native

    def snapshot(engine, *args, **kwargs):
        with patch.object(np.linalg, "norm", norm):
            return build_snapshot(engine, *args, **kwargs)

    with patch.object(EvolutionEngine, "_build_snapshot", snapshot):
        result = run(stable=True)
    return {"calls": calls, **result}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    native, reference = (trace(flag) for flag in (False, True))
    if native["selection"] != reference["selection"]:
        raise ValueError("diagnostic reference changed selection")
    if native["result"]["lineage"] != reference["result"]["lineage"]:
        raise ValueError("diagnostic reference changed lineage")
    record = {
        "platform": platform.platform(),
        "python": sys.version,
        "numpy": np.__version__,
        "build": np.show_config(mode="dicts"),
        "native": native,
        "reference": reference,
    }
    with args.output.open("x", encoding="utf-8") as handle:
        json.dump(record, handle, separators=(",", ":"))
        handle.write("\n")


if __name__ == "__main__":
    main()
