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

_LITERATURE_CASES: dict[str, Any] = {}


def _literature_cases() -> dict[str, Any]:
    if not _LITERATURE_CASES:
        from genevra.literature.cases import (
            case_a_plasticity_evolvability_tradeoff,
            case_b_volatility_and_plasticity,
            case_c_history_dependence,
            case_d_learning_strategy_predicts_potential,
        )

        _LITERATURE_CASES.update(
            {
                "case_a": case_a_plasticity_evolvability_tradeoff,
                "case_b": case_b_volatility_and_plasticity,
                "case_c": case_c_history_dependence,
                "case_d": case_d_learning_strategy_predicts_potential,
            }
        )
    return _LITERATURE_CASES


def _cmd_literature(args: argparse.Namespace) -> int:
    cases = _literature_cases()
    if args.output:
        payload = []
        for case_id, factory in cases.items():
            claim, spec, _conditions = factory(population_size=2, generations=1, seeds=(0, 1))
            payload.append({"case_id": case_id, "claim": claim.to_dict(), "spec": spec.to_dict()})
        with open(args.output, "w") as f:
            json.dump(payload, f, indent=2)
        print(f"wrote {args.output}")
        return 0
    for case_id, factory in cases.items():
        claim, _spec, _conditions = factory(population_size=2, generations=1, seeds=(0, 1))
        print(f"{case_id}: {claim.claim_id} ({claim.source_reference})")
        print(f"  {claim.claim_text}")
    return 0


def _cmd_reproduce(args: argparse.Namespace) -> int:
    from genevra.literature.falsification import (
        generate_falsification_experiments,
        generate_falsification_hypotheses,
    )
    from genevra.literature.report import build_reproduction_report
    from genevra.literature.runner import LiteratureReproductionRunner

    cases = _literature_cases()
    if args.case_id not in cases:
        print(f"unknown case_id {args.case_id!r}; choices: {list(cases)}", file=sys.stderr)
        return 1
    claim, spec, conditions = cases[args.case_id](
        population_size=args.population_size,
        generations=args.generations,
        seeds=tuple(range(args.seeds)),
    )
    rng = np.random.default_rng(args.seed)
    result = LiteratureReproductionRunner().run(spec, conditions, rng, parallel=args.parallel)
    hypotheses = generate_falsification_hypotheses(
        spec.control_condition + "_vs_" + spec.treatment_condition,
        spec.primary_metric,
        result.observed_direction,
    )
    report = build_reproduction_report(claim, spec, result, falsification_hypotheses=hypotheses[:1])
    if args.output:
        with open(args.output, "w") as f:
            json.dump(report.to_dict(), f, indent=2)
        print(f"wrote {args.output}")
    else:
        print(report.to_text())
    del generate_falsification_experiments
    return 0


def _cmd_falsify(args: argparse.Namespace) -> int:
    from genevra.literature.falsification import (
        generate_falsification_experiments,
        generate_falsification_hypotheses,
    )

    hypotheses = generate_falsification_hypotheses(
        args.independent_variable, args.dependent_variable, args.observed_direction
    )
    proposals = generate_falsification_experiments(hypotheses)
    payload = {
        "hypotheses": [
            {"hypothesis_id": h.hypothesis_id, "statement": h.statement} for h in hypotheses
        ],
        "proposed_experiments": [
            {
                "hypothesis_id": p.hypothesis_id,
                "conditions": list(p.conditions),
                "sample_size": p.sample_size,
                "generation_budget": p.generation_budget,
            }
            for p in proposals
        ],
    }
    if args.output:
        with open(args.output, "w") as f:
            json.dump(payload, f, indent=2)
        print(f"wrote {args.output}")
    else:
        for h in hypotheses:
            print(f"- {h.statement}")
    return 0


def _load_lineage_events(data: dict[str, Any]) -> Any:
    from genevra.evolution.lineage import LineageEvent

    events = []
    for raw in data.get("lineage", []):
        events.append(
            LineageEvent(
                individual_id=raw["individual_id"],
                parent_ids=tuple(raw["parent_ids"]),
                generation=raw["generation"],
                genome_hash=raw["genome_hash"],
                death_generation=raw.get("death_generation"),
                reproduced=raw.get("reproduced", False),
                learning_strategy=tuple(raw.get("learning_strategy", (0.0, 1.0, 0.0))),
            )
        )
    return events


def _build_tracker(events: Any) -> Any:
    from genevra.evolution.lineage import LineageTracker

    tracker = LineageTracker()
    for event in events:
        tracker._events[event.individual_id] = event  # noqa: SLF001 - CLI-only reconstruction
    return tracker


def _cmd_open_endedness(args: argparse.Namespace) -> int:
    from genevra.innovation.analyzer import OpenEndednessAnalyzer
    from genevra.innovation.dependency_graph import build_innovation_dependency_graph
    from genevra.innovation.report import build_open_endedness_lab_report

    with open(args.result_path) as f:
        data = json.load(f)
    trajectory = data.get("trajectory") or []
    if not trajectory:
        print("empty trajectory: nothing to analyze")
        return 1
    events = _load_lineage_events(data)
    tracker = _build_tracker(events)
    rng = np.random.default_rng(args.seed)
    analysis = OpenEndednessAnalyzer().analyze(trajectory, events, tracker, rng)
    graph = None
    if analysis.innovation_events is not None:
        graph = build_innovation_dependency_graph(analysis.innovation_events, tracker)
    report = build_open_endedness_lab_report(analysis, dependency_graph=graph)
    if args.output:
        with open(args.output, "w") as f:
            json.dump(report.to_dict(), f, indent=2)
        print(f"wrote {args.output}")
    else:
        print(report.to_text())
    return 0


def _cmd_innovation(args: argparse.Namespace) -> int:
    from genevra.innovation.dependency_graph import build_innovation_dependency_graph
    from genevra.innovation.events import detect_innovation_events

    with open(args.result_path) as f:
        data = json.load(f)
    events = _load_lineage_events(data)
    tracker = _build_tracker(events)
    detected = detect_innovation_events(
        events, tracker, z_threshold=args.z_threshold, min_cohort_size=args.min_cohort_size
    )
    graph = build_innovation_dependency_graph(detected, tracker)
    if args.output:
        payload = {
            "events": [e.to_dict() for e in detected],
            "n_dependency_edges": len(graph.edges),
        }
        with open(args.output, "w") as f:
            json.dump(payload, f, indent=2)
        print(f"wrote {args.output}")
    else:
        print(
            f"{len(detected)} innovation event(s) detected, {len(graph.edges)} dependency edge(s)"
        )
        for event in detected:
            print(
                f"  gen={event.generation} lineage={event.lineage} "
                f"novelty_score={event.novelty_score:.3f} descendants={event.descendant_count}"
            )
    return 0


def _cmd_activity(args: argparse.Namespace) -> int:
    from genevra.innovation.activity import build_activity_report

    with open(args.result_path) as f:
        data = json.load(f)
    trajectory = data.get("trajectory") or []
    if not trajectory:
        print("empty trajectory: nothing to analyze")
        return 1
    events = _load_lineage_events(data)
    report = build_activity_report(trajectory, events, np.random.default_rng(args.seed))
    if args.output:
        with open(args.output, "w") as f:
            json.dump(report.to_dict(), f, indent=2)
        print(f"wrote {args.output}")
    else:
        print(f"n_generations_observed={report.n_generations_observed}")
        print(f"lineage_persistence={report.lineage_persistence:.3f}")
        print(f"diversity_growth_decay_slope={report.diversity_growth_decay_slope:.4g}")
        print(f"strategy_turnover_series={list(report.strategy_turnover_series)}")
    return 0


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

    literature_parser = subparsers.add_parser(
        "literature", help="list the initial literature-inspired reproduction cases"
    )
    literature_parser.add_argument("--output", type=str, default=None)
    literature_parser.set_defaults(func=_cmd_literature)

    reproduce_parser = subparsers.add_parser(
        "reproduce", help="run a literature-inspired reproduction case end-to-end"
    )
    reproduce_parser.add_argument(
        "case_id", type=str, choices=["case_a", "case_b", "case_c", "case_d"]
    )
    reproduce_parser.add_argument("--population-size", type=int, default=16)
    reproduce_parser.add_argument("--generations", type=int, default=20)
    reproduce_parser.add_argument("--seeds", type=int, default=8, help="number of seeds (0..N-1)")
    reproduce_parser.add_argument("--seed", type=int, default=0, help="RNG seed for the statistics")
    reproduce_parser.add_argument("--parallel", action="store_true")
    reproduce_parser.add_argument("--output", type=str, default=None)
    reproduce_parser.set_defaults(func=_cmd_reproduce)

    falsify_parser = subparsers.add_parser(
        "falsify", help="generate falsification hypotheses/experiments for an observed association"
    )
    falsify_parser.add_argument("independent_variable", type=str)
    falsify_parser.add_argument("dependent_variable", type=str)
    falsify_parser.add_argument(
        "--observed-direction", type=str, default=None, dest="observed_direction"
    )
    falsify_parser.add_argument("--output", type=str, default=None)
    falsify_parser.set_defaults(func=_cmd_falsify)

    open_endedness_parser = subparsers.add_parser(
        "open-endedness", help="run the open-endedness lab analysis on a stored result"
    )
    open_endedness_parser.add_argument("result_path", type=str)
    open_endedness_parser.add_argument("--seed", type=int, default=0)
    open_endedness_parser.add_argument("--output", type=str, default=None)
    open_endedness_parser.set_defaults(func=_cmd_open_endedness)

    innovation_parser = subparsers.add_parser(
        "innovation", help="detect innovation events and their lineage dependency graph"
    )
    innovation_parser.add_argument("result_path", type=str)
    innovation_parser.add_argument("--z-threshold", type=float, default=2.0, dest="z_threshold")
    innovation_parser.add_argument("--min-cohort-size", type=int, default=3, dest="min_cohort_size")
    innovation_parser.add_argument("--output", type=str, default=None)
    innovation_parser.set_defaults(func=_cmd_innovation)

    activity_parser = subparsers.add_parser(
        "activity", help="compute the evolutionary activity report for a stored result"
    )
    activity_parser.add_argument("result_path", type=str)
    activity_parser.add_argument("--seed", type=int, default=0)
    activity_parser.add_argument("--output", type=str, default=None)
    activity_parser.set_defaults(func=_cmd_activity)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    result: int = args.func(args)
    return result


if __name__ == "__main__":
    sys.exit(main())
