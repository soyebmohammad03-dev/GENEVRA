"""`genevra` command-line entry point: run an experiment, compare
conditions, analyze a stored result, or inspect one — without editing
Python source for the common cases. Plain `argparse` subcommands; no new
CLI-framework dependency.
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any

from genevra.analysis.stagnation import StagnationAnalyzer
from genevra.utils.logging import configure_logging


def _build_baseline_experiment_config(seed: int) -> Any:
    # Imported lazily: experiments/baseline.py lives outside the package
    # and is only needed for the `run` subcommand.
    import importlib.util
    from pathlib import Path

    baseline_path = Path(__file__).resolve().parents[2] / "experiments" / "baseline.py"
    spec = importlib.util.spec_from_file_location("genevra_baseline", baseline_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"could not load {baseline_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.build_config(seed)


def _cmd_run(args: argparse.Namespace) -> int:
    from genevra.experiments.runner import ExperimentRunner

    configure_logging()
    config = _build_baseline_experiment_config(args.seed)
    result = ExperimentRunner(config).run()
    print(f"status={result.status} generations={result.generations_completed}")
    if args.output:
        with open(args.output, "w") as f:
            json.dump(result.to_dict(), f, indent=2)
        print(f"wrote {args.output}")
    return 0


def _cmd_analyze(args: argparse.Namespace) -> int:
    with open(args.result_path) as f:
        data = json.load(f)
    trajectory = data["trajectory"]
    if not trajectory:
        print("empty trajectory: nothing to analyze")
        return 1
    report = StagnationAnalyzer().analyze(trajectory)
    print(f"stagnation_score={report.stagnation_score:.2f}")
    print(f"contributing_signals={list(report.contributing_signals)}")
    print(f"fitness_plateaued={report.fitness_plateaued} (NOT counted toward stagnation_score)")
    print(f"detected_at_generation={report.detected_at_generation}")
    return 0


def _cmd_inspect(args: argparse.Namespace) -> int:
    with open(args.result_path) as f:
        data = json.load(f)
    print(f"name={data.get('name')} seed={data.get('seed')} status={data.get('status')}")
    if data.get("failure"):
        print(f"failure={data['failure']}")
    print(f"generations_completed={data.get('generations_completed')}")
    print(f"final_population_size={data.get('final_population_size')}")
    trajectory = data.get("trajectory", [])
    if trajectory:
        last = trajectory[-1]
        print(f"final_fitness_mean={last['fitness_summary']['mean']:.3f}")
        print(f"final_genotypic_diversity={last['genotypic_diversity']:.3f}")
        print(f"final_behavioral_diversity={last['behavioral_diversity']:.3f}")
    lineage = data.get("lineage", [])
    print(f"lineage_records={len(lineage)}")
    return 0


def _cmd_compare(args: argparse.Namespace) -> int:
    print(
        "genevra compare currently points to the named controlled experiment scripts:\n"
        "  python experiments/exp1_isolated_vs_shared.py\n"
        "  python experiments/exp2_static_vs_changing.py\n"
        "  python experiments/exp3_fixed_vs_heritable_mutation.py\n"
        "Each accepts --seeds and --output; see docs/experiments.md."
    )
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="genevra")
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_parser = subparsers.add_parser("run", help="run the baseline experiment")
    run_parser.add_argument("--seed", type=int, default=0)
    run_parser.add_argument("--output", type=str, default=None)
    run_parser.set_defaults(func=_cmd_run)

    analyze_parser = subparsers.add_parser("analyze", help="stagnation-analyze a stored result")
    analyze_parser.add_argument("result_path", type=str)
    analyze_parser.set_defaults(func=_cmd_analyze)

    inspect_parser = subparsers.add_parser("inspect", help="print a summary of a stored result")
    inspect_parser.add_argument("result_path", type=str)
    inspect_parser.set_defaults(func=_cmd_inspect)

    compare_parser = subparsers.add_parser(
        "compare", help="list the controlled comparison experiments"
    )
    compare_parser.set_defaults(func=_cmd_compare)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    result: int = args.func(args)
    return result


if __name__ == "__main__":
    sys.exit(main())
