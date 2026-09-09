"""Baseline evolutionary experiment: a small population evolving in a
GridWorld for a modest number of generations.

Demonstrates the full Phase 3 + Phase 4 pipeline end to end — reproduction,
mutation, selection, learning, metric collection, and lineage tracking —
at a size that runs on a laptop in a few seconds. This is a demonstration
substrate for exercising the machinery, not a claim about open-ended
evolution, emergent intelligence, or evolved evolvability; see
docs/experiments.md for what a run like this does and does not show.

Usage:
    python experiments/baseline.py --seed 0
    python experiments/baseline.py --seed 0 --output results/baseline_seed0.json
    python experiments/baseline.py --seed 0 --evolvability-samples 12
"""

from __future__ import annotations

import argparse
import json
import time

import numpy as np

from genevra.arrays import FloatArray
from genevra.evolution.engine import EvolutionConfig
from genevra.evolution.fitness import SurvivalResourceFitness
from genevra.evolution.population import PopulationConfig
from genevra.evolution.reproduction import PopulationReproductionConfig
from genevra.evolution.selection import ElitistSelection, TournamentSelection
from genevra.experiments.config import ExperimentConfig
from genevra.experiments.runner import ExperimentRunner
from genevra.organism.genome import ControllerArchitecture, Genome
from genevra.organism.learning import NoLearning
from genevra.organism.mutation import GaussianMutation
from genevra.organism.organism import OrganismConfig
from genevra.simulation.grid_world import GridWorldConfig
from genevra.utils.logging import configure_logging

VIEW_RADIUS = 1
MEMORY_SIZE = 4
_GRID_FEATURES = (2 * VIEW_RADIUS + 1) ** 2 * 2
INPUT_SIZE = _GRID_FEATURES + 2 + MEMORY_SIZE  # + own energy, last action


def build_config(seed: int) -> ExperimentConfig:
    architecture = ControllerArchitecture(input_size=INPUT_SIZE, hidden_size=8, output_size=6)
    organism_config = OrganismConfig(
        view_radius=VIEW_RADIUS, memory_size=MEMORY_SIZE, initial_energy=30.0
    )
    population_config = PopulationConfig(
        size=24,
        architecture=architecture,
        organism_config=organism_config,
        initial_mutation_rate=0.15,
        initial_mutation_sigma=0.2,
    )
    environment_config = GridWorldConfig(
        width=15,
        height=15,
        view_radius=VIEW_RADIUS,
        resource_density=0.15,
        resource_energy_value=6.0,
        resource_regen_prob=0.03,
        obstacle_density=0.1,
        max_steps=80,
    )
    evolution_config = EvolutionConfig(
        generations=15,
        steps_per_lifetime=80,
        environment_config=environment_config,
        population_config=population_config,
        fitness_function=SurvivalResourceFitness(survival_weight=0.2, resource_weight=1.0),
        selection_strategy=ElitistSelection(
            TournamentSelection(tournament_size=3), elite_fraction=0.1
        ),
        reproduction=PopulationReproductionConfig(
            energy_threshold=5.0, mutation_operator=GaussianMutation()
        ),
        learning_rule_factory=NoLearning,
        seed=seed,
    )
    return ExperimentConfig(name="baseline", evolution=evolution_config)


def _print_evolvability(
    config: ExperimentConfig, runner: ExperimentRunner, seed: int, num_samples: int
) -> None:
    from genevra.evolution.lifetime import run_single_lifetime
    from genevra.metrics.behavior import behavioral_signature
    from genevra.metrics.diversity import EuclideanDistance
    from genevra.metrics.evolvability import EvolvabilityAnalyzer

    assert runner.engine is not None
    if not runner.engine.population.individuals:
        print("evolvability: skipped (final population is empty)")
        return

    target_genome = runner.engine.population.individuals[0].genome
    eval_rng = np.random.default_rng(seed + 1)
    eval_steps = min(40, config.evolution.steps_per_lifetime)

    def behavioral_evaluator(genome: Genome) -> FloatArray:
        observations = run_single_lifetime(
            genome=genome,
            environment_config=config.evolution.environment_config,
            organism_config=config.evolution.population_config.organism_config,
            learning_rule=config.evolution.learning_rule_factory(),
            env_seed=seed,
            organism_seed=int(eval_rng.integers(0, 2**31 - 1)),
            max_steps=eval_steps,
        )
        return behavioral_signature(observations)

    analyzer = EvolvabilityAnalyzer(
        mutation_operator=GaussianMutation(),
        behavioral_evaluator=behavioral_evaluator,
        distance=EuclideanDistance(),
        num_samples=num_samples,
    )
    report = analyzer.analyze(target_genome, eval_rng)
    print(
        f"evolvability: mean_behavioral_distance={report.mean_behavioral_distance:.3f} "
        f"std={report.behavioral_distance_std:.3f} viable_fraction={report.viable_fraction:.2f} "
        f"num_samples={report.num_samples}"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument(
        "--output", type=str, default=None, help="path to write the full result as JSON"
    )
    parser.add_argument(
        "--evolvability-samples",
        type=int,
        default=0,
        help="if > 0, run an on-demand mutation-neighborhood evolvability analysis on one "
        "final-population genome using this many samples (off by default: not a per-run cost)",
    )
    args = parser.parse_args()

    configure_logging()
    config = build_config(args.seed)
    runner = ExperimentRunner(config)

    start = time.perf_counter()
    result = runner.run()
    elapsed = time.perf_counter() - start

    print(
        f"status={result.status} generations={result.generations_completed} "
        f"final_population={result.final_population_size} elapsed={elapsed:.2f}s"
    )
    if result.trajectory:
        last = result.trajectory[-1]
        print(
            f"final: mean_fitness={last['fitness_summary']['mean']:.3f} "
            f"genotypic_diversity={last['genotypic_diversity']:.3f} "
            f"behavioral_diversity={last['behavioral_diversity']:.3f} "
            f"mean_novelty={last['mean_novelty']:.3f} "
            f"survival_rate={last['survival_rate']:.2f} "
            f"mean_mutation_rate={last['mean_mutation_rate']:.3f}"
        )

    if args.evolvability_samples > 0:
        _print_evolvability(config, runner, args.seed, args.evolvability_samples)

    if args.output:
        with open(args.output, "w") as f:
            json.dump(result.to_dict(), f, indent=2)
        print(f"wrote full result to {args.output}")


if __name__ == "__main__":
    main()
