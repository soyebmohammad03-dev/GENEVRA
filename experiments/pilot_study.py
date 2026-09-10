"""GENEVRA PILOT STUDY (Phase 8.19): validating the research pipeline
described in `docs/research_protocol.md` — NOT a claim of a scientific
discovery.

Compares the three primary learning conditions (A. no learning, B. fixed
learning, C. evolvable learning — see
`genevra.experiments.conditions.LearningCondition`) under two of the
protocol's secondary environment regimes (stable, changing), at a scale
small enough to run in well under a minute on a laptop: this establishes
that the full pipeline (conditions -> `ComparisonRunner` ->
`validate_comparison` -> `build_research_report`) works end to end and
produces genuine, reproducible numbers — not that any hypothesis is
confirmed. See the printed/written report's `interpretation` field,
which is intentionally left for a human to fill in.
"""

from __future__ import annotations

import argparse
import json
from collections.abc import Callable

import numpy as np

from genevra.analysis.comparison import ComparisonRunner, validate_comparison
from genevra.analysis.report import build_research_report
from genevra.evolution.engine import EvolutionConfig
from genevra.evolution.fitness import SurvivalResourceFitness
from genevra.evolution.population import PopulationConfig
from genevra.evolution.reproduction import PopulationReproductionConfig
from genevra.evolution.selection import TournamentSelection
from genevra.experiments.conditions import LearningCondition, apply_learning_condition
from genevra.experiments.config import ExperimentConfig
from genevra.organism.genome import ControllerArchitecture
from genevra.organism.learning import NoLearning
from genevra.organism.mutation import GaussianMutation
from genevra.organism.organism import OrganismConfig
from genevra.simulation.dynamics import EnvironmentRegime, PeriodicDynamics
from genevra.simulation.grid_world import GridWorldConfig
from genevra.simulation.types import Action

VIEW_RADIUS = 1
MEMORY_SIZE = 4
_GRID_FEATURES = (2 * VIEW_RADIUS + 1) ** 2 * 2
INPUT_SIZE = _GRID_FEATURES + 2 + MEMORY_SIZE

GENERATIONS = 12
POPULATION_SIZE = 12
STEPS_PER_LIFETIME = 40
WORLD_SIZE = 12


def _base_config(seed: int, dynamics: object | None) -> EvolutionConfig:
    architecture = ControllerArchitecture(
        input_size=INPUT_SIZE, hidden_size=8, output_size=len(Action)
    )
    organism_config = OrganismConfig(
        view_radius=VIEW_RADIUS, memory_size=MEMORY_SIZE, initial_energy=25.0
    )
    population_config = PopulationConfig(
        size=POPULATION_SIZE, architecture=architecture, organism_config=organism_config
    )
    environment_config = GridWorldConfig(
        width=WORLD_SIZE,
        height=WORLD_SIZE,
        view_radius=VIEW_RADIUS,
        max_steps=STEPS_PER_LIFETIME,
        dynamics=dynamics,  # type: ignore[arg-type]
    )
    return EvolutionConfig(
        generations=GENERATIONS,
        steps_per_lifetime=STEPS_PER_LIFETIME,
        environment_config=environment_config,
        population_config=population_config,
        fitness_function=SurvivalResourceFitness(),
        selection_strategy=TournamentSelection(tournament_size=3),
        reproduction=PopulationReproductionConfig(
            energy_threshold=2.0, mutation_operator=GaussianMutation()
        ),
        learning_rule_factory=NoLearning,
        seed=seed,
    )


_CHANGING_DYNAMICS = PeriodicDynamics(
    regime_a=EnvironmentRegime(resource_regen_prob=0.03),
    regime_b=EnvironmentRegime(resource_regen_prob=0.0),
    period=10,
)


def make_condition_factory(
    condition: LearningCondition, changing_environment: bool
) -> Callable[[int], ExperimentConfig]:
    dynamics = _CHANGING_DYNAMICS if changing_environment else None
    regime_name = "changing" if changing_environment else "stable"

    def factory(seed: int) -> ExperimentConfig:
        base = _base_config(seed, dynamics)
        evolution = apply_learning_condition(base, condition)
        return ExperimentConfig(name=f"{condition.value}__{regime_name}", evolution=evolution)

    return factory


def _fitness_extractor(g: dict) -> float:
    return float(g["fitness_summary"]["mean"])


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seeds", type=int, nargs="+", default=[0, 1, 2, 3, 4])
    parser.add_argument("--output", type=str, default="experiments/results/pilot_v1_results.json")
    parser.add_argument(
        "--report-output", type=str, default="experiments/results/pilot_v1_report.json"
    )
    args = parser.parse_args()

    conditions = {
        f"{condition.value}__{regime}": make_condition_factory(condition, changing)
        for condition in LearningCondition
        for regime, changing in (("stable", False), ("changing", True))
    }

    runner = ComparisonRunner(conditions=conditions, seeds=args.seeds)
    result = runner.run()

    validation = validate_comparison(result)
    print(f"seeds={result.seeds}")
    print(f"failures={len(result.failures())}")
    print(f"validation.ok()={validation.ok()}")
    for warning in validation.warnings:
        print(f"  WARNING: {warning}")
    for error in validation.errors:
        print(f"  ERROR: {error}")

    for condition_name, runs in result.conditions.items():
        final_fitness = [
            r["trajectory"][-1]["fitness_summary"]["mean"] for r in runs if r["trajectory"]
        ]
        final_novelty = [
            r["trajectory"][-1]["instantaneous_novelty"] for r in runs if r["trajectory"]
        ]
        final_diversity = [
            r["trajectory"][-1]["behavioral_diversity"] for r in runs if r["trajectory"]
        ]
        print(
            f"[{condition_name:28s}] "
            f"fitness={np.mean(final_fitness):8.3f} "
            f"novelty={np.mean(final_novelty):7.3f} "
            f"diversity={np.mean(final_diversity):7.3f} "
            f"n={len(runs)}"
        )

    report = build_research_report(
        result,
        question=(
            "Can evolutionary systems evolve learning strategies that improve "
            "adaptation and evolutionary novelty?"
        ),
        hypothesis=(
            "Populations with evolvable learning strategy (condition C) show "
            "measurably different fitness/novelty/diversity dynamics than "
            "no-learning (A) or fixed-learning (B) populations, under matched "
            "conditions."
        ),
        metric_extractor=_fitness_extractor,
        metric_name="fitness_summary.mean (final generation)",
        secondary_factors=["stable vs. changing environment (PeriodicDynamics)"],
        rng=np.random.default_rng(0),
    )

    print("\n=== Pairwise effect sizes (Cohen's d, final-generation fitness) ===")
    for pair in report.pairwise_comparisons:
        print(
            f"  {pair.condition_a} vs {pair.condition_b}: "
            f"d={pair.effect_size.cohens_d:6.3f} "
            f"(mean_diff={pair.effect_size.mean_difference:7.3f})"
        )

    if args.output:
        with open(args.output, "w") as f:
            json.dump(result.conditions, f, indent=2)
        print(f"\nwrote {args.output}")

    if args.report_output:
        with open(args.report_output, "w") as f:
            json.dump(report.to_dict(), f, indent=2)
        print(f"wrote {args.report_output}")


if __name__ == "__main__":
    main()
