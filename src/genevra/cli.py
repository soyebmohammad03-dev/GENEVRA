"""`genevra` command-line entry point: run an experiment, compare
conditions, analyze a stored result, or inspect one — without editing
Python source for the common cases. Plain `argparse` subcommands; no new
CLI-framework dependency.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import TYPE_CHECKING, Any

import numpy as np

from genevra.analysis.stagnation import StagnationAnalyzer
from genevra.utils.logging import configure_logging

if TYPE_CHECKING:
    from genevra.discovery.correlation import RunSummary
    from genevra.discovery.report import DiscoveryReport


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


_DISCOVERY_VARIABLES = (
    "mean_mutation_rate",
    "mean_mutation_sigma",
    "final_fitness_mean",
    "final_novelty",
    "final_genotypic_diversity",
    "final_behavioral_diversity",
)


def _load_stored_results(results_dir: str) -> list[dict[str, Any]]:
    paths = sorted(Path(results_dir).glob("*.json"))
    if not paths:
        raise FileNotFoundError(f"no *.json result files found in {results_dir}")
    results = []
    for path in paths:
        with open(path) as f:
            results.append(json.load(f))
    return results


def _run_summary(data: dict[str, Any]) -> RunSummary | None:
    from genevra.discovery.correlation import RunSummary

    trajectory = data.get("trajectory") or []
    if data.get("status") != "completed" or not trajectory:
        return None
    last = trajectory[-1]
    variables = {
        "mean_mutation_rate": float(last["mean_mutation_rate"]),
        "mean_mutation_sigma": float(last["mean_mutation_sigma"]),
        "final_fitness_mean": float(last["fitness_summary"]["mean"]),
        "final_novelty": float(last["instantaneous_novelty"]),
        "final_genotypic_diversity": float(last["genotypic_diversity"]),
        "final_behavioral_diversity": float(last["behavioral_diversity"]),
    }
    return RunSummary(experiment=str(data["name"]), seed=int(data["seed"]), variables=variables)


def _discover(results_dir: str, seed: int) -> DiscoveryReport:
    import itertools

    from genevra.discovery.correlation import correlation_discovery
    from genevra.discovery.followup import generate_followup_experiment
    from genevra.discovery.hypothesis import (
        deduplicate_hypotheses,
        hypotheses_from_correlations,
        hypotheses_from_recurring_phenomena,
        rank_hypotheses,
    )
    from genevra.discovery.multiple_testing import benjamini_hochberg
    from genevra.discovery.phenomena import PhenomenonDetector
    from genevra.discovery.report import build_discovery_report

    results = _load_stored_results(results_dir)
    run_summaries = [s for s in (_run_summary(r) for r in results) if s is not None]

    detector = PhenomenonDetector()
    observations = [
        observation
        for r in results
        if r.get("status") == "completed" and r.get("trajectory")
        for observation in detector.detect(r["trajectory"], str(r["name"]), int(r["seed"]))
    ]

    hypotheses = list(hypotheses_from_recurring_phenomena(observations))
    if len(run_summaries) >= 3:
        pairs = list(itertools.combinations(_DISCOVERY_VARIABLES, 2))
        rng = np.random.default_rng(seed)
        correlations = correlation_discovery(run_summaries, pairs, rng)
        fdr = benjamini_hochberg([c.p_value for c in correlations])
        hypotheses += hypotheses_from_correlations(correlations, fdr)
    hypotheses = rank_hypotheses(deduplicate_hypotheses(hypotheses))
    follow_ups = [generate_followup_experiment(h) for h in hypotheses]

    return build_discovery_report(
        observed_phenomena=observations,
        candidate_hypotheses=hypotheses,
        contradicting_evidence=[],
        follow_up_experiments=follow_ups,
        hypothesis_evaluations=[],
    )


def _cmd_discover(args: argparse.Namespace) -> int:
    report = _discover(args.results_dir, args.seed)
    if args.output:
        with open(args.output, "w") as f:
            json.dump(report.to_dict(), f, indent=2)
        print(f"wrote {args.output}")
    else:
        print(report.to_text())
    return 0


def _cmd_hypothesis(args: argparse.Namespace) -> int:
    report = _discover(args.results_dir, args.seed)
    if not report.candidate_hypotheses:
        print("no candidate hypotheses found")
        return 0
    for hypothesis in report.candidate_hypotheses:
        print(
            f"[{hypothesis.evidence_score:.3f}] {hypothesis.hypothesis_id}: {hypothesis.statement}"
        )
    return 0


def _cmd_replicate(args: argparse.Namespace) -> int:
    from genevra.discovery.replication import EvidenceSet, ReplicationRunner

    def _values(results_dir: str) -> tuple[tuple[int, ...], tuple[float, ...]]:
        results = _load_stored_results(results_dir)
        seeds, values = [], []
        for data in results:
            trajectory = data.get("trajectory") or []
            if data.get("status") != "completed" or not trajectory:
                continue
            node: Any = trajectory[-1]
            for part in args.dependent_variable.split("."):
                node = node[part]
            seeds.append(int(data["seed"]))
            values.append(float(node))
        return tuple(seeds), tuple(values)

    original_seeds, original_values = _values(args.original_dir)
    replication_seeds, replication_values = _values(args.replication_dir)
    original = EvidenceSet(seeds=original_seeds, values=original_values, source="original")
    replication = EvidenceSet(
        seeds=replication_seeds, values=replication_values, source="replication"
    )
    result = ReplicationRunner().evaluate(
        args.hypothesis_id, original, replication, np.random.default_rng(args.seed)
    )
    print(f"hypothesis_id={result.hypothesis_id}")
    print(f"original_mean={result.original_mean:.4f} (n={len(original_seeds)})")
    print(
        f"replication_mean={result.replication_mean:.4f} "
        f"ci=[{result.replication_ci.low:.4f}, {result.replication_ci.high:.4f}] "
        f"(n={len(replication_seeds)})"
    )
    print(f"replicated={result.replicated}")
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

    discover_parser = subparsers.add_parser(
        "discover",
        help="scan a directory of stored experiment results for phenomena and hypotheses",
    )
    discover_parser.add_argument("results_dir", type=str)
    discover_parser.add_argument("--seed", type=int, default=0)
    discover_parser.add_argument("--output", type=str, default=None)
    discover_parser.set_defaults(func=_cmd_discover)

    hypothesis_parser = subparsers.add_parser(
        "hypothesis", help="print ranked candidate hypotheses for a directory of stored results"
    )
    hypothesis_parser.add_argument("results_dir", type=str)
    hypothesis_parser.add_argument("--seed", type=int, default=0)
    hypothesis_parser.set_defaults(func=_cmd_hypothesis)

    replicate_parser = subparsers.add_parser(
        "replicate",
        help="compare original vs. independent-seed replication evidence for one variable",
    )
    replicate_parser.add_argument("original_dir", type=str)
    replicate_parser.add_argument("replication_dir", type=str)
    replicate_parser.add_argument("--hypothesis-id", type=str, default="unnamed")
    replicate_parser.add_argument("--dependent-variable", type=str, default="fitness_summary.mean")
    replicate_parser.add_argument("--seed", type=int, default=0)
    replicate_parser.set_defaults(func=_cmd_replicate)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    result: int = args.func(args)
    return result


if __name__ == "__main__":
    sys.exit(main())
