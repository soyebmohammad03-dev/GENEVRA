"""Trace seed-zero parent selection under the native and stable sort policies."""

import argparse
import hashlib
import json
import os
import platform
import sys
from contextlib import redirect_stdout
from dataclasses import replace
from pathlib import Path

import numpy as np

from genevra.evolution.selection import ElitistSelection, TournamentSelection
from genevra.experiments._resources import load_experiment_script
from genevra.experiments.runner import ExperimentRunner


def fingerprint(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()


class SelectionTrace(ElitistSelection):
    """Observe selection without advancing its RNG; optionally change the tie rule."""

    def __init__(self, stable):
        super().__init__(TournamentSelection(tournament_size=3), elite_fraction=0.1)
        self.stable = stable
        self.rows = []

    def select(self, fitness_scores, num_parents, rng):
        scores = np.asarray(fitness_scores, dtype=np.float64)
        count = min(num_parents, int(np.ceil(len(scores) * self._elite_fraction)))
        native_elites = np.argsort(-scores)[:count].tolist()
        stable_elites = np.argsort(-scores, kind="stable")[:count].tolist()
        before = fingerprint(rng.bit_generator.state)
        if self.stable:
            parents = stable_elites + self._base.select(fitness_scores, num_parents - count, rng)
        else:
            parents = super().select(fitness_scores, num_parents, rng)
        self.rows.append(
            {
                "fitness": scores.tolist(),
                "native_elites": native_elites,
                "stable_elites": stable_elites,
                "parents": parents,
                "rng_before": before,
                "rng_after": fingerprint(rng.bit_generator.state),
            }
        )
        return parents


def run(stable):
    selection = SelectionTrace(stable)
    baseline = load_experiment_script("baseline.py").build_config(0)
    config = replace(baseline, evolution=replace(baseline.evolution, selection_strategy=selection))
    result = ExperimentRunner(config).run().to_dict()
    if result["status"] != "completed" or len(selection.rows) != 15:
        raise RuntimeError(f"incomplete diagnostic: {result['failure']}")
    return {"selection": selection.rows, "result": result}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    threads = ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "PYTHONHASHSEED")
    record = {
        "platform": platform.platform(),
        "python": sys.version,
        "numpy": np.__version__,
        "environment": {key: os.environ.get(key) for key in threads},
        "numpy_build": np.show_config(mode="dicts"),
        "rng": type(np.random.default_rng(0).bit_generator).__name__,
        "seed": 0,
    }
    for label, stable in (("native", False), ("stable", True)):
        first = run(stable)
        if first != run(stable):
            raise RuntimeError(f"{label} diagnostic did not repeat within the same environment")
        record[label] = first
    with args.output.open("x", encoding="utf-8") as handle:
        json.dump(record, handle, indent=2)
        handle.write("\n")
    with redirect_stdout(sys.stderr):
        print("Both policies repeated exactly within this environment.")


if __name__ == "__main__":
    main()
