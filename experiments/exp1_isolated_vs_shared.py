"""EXPERIMENT 1: Isolated vs. Shared Environment.

Hypothesis: allowing organisms to coexist in one shared environment
(competing for the same limited resources, colliding spatially, subject
to the same temporal state) produces a different final-population
genotypic diversity than running an approximately equal total
organism-lifetime-step budget as fully isolated, single-organism
episodes.

Independent variable: isolated (`genevra.evolution.engine.EvolutionEngine`
+ `GridWorld`, one organism per episode, discrete non-overlapping
generations) vs. shared (`genevra.evolution.continuous.ContinuousEvolutionEngine`
+ `SharedGridWorld`, many organisms coexisting, overlapping generations).

Dependent measurement: final-population genotypic diversity (mean
pairwise Euclidean distance between `controller_weights` vectors) — the
one metric directly comparable across both engines' data models. Full
behavioral-diversity comparison is NOT attempted here: the two engines
don't share a per-generation `LifetimeObservations` pipeline (the
continuous engine's organisms don't have discrete "lifetimes" with a
start/end to summarize the same way), so behavioral diversity numbers
from the two conditions would not be measuring the same thing. See
docs/ecology.md.

Controlled variables: controller architecture, per-organism config,
mutation operator and initial mutation parameters, an approximately
matched total organism-lifetime-step budget, and the seed sequence
(shared across both conditions).

This is an infrastructure-validation experiment: it demonstrates that the
isolated and shared pipelines both run, are both reproducible, and can be
compared on a shared metric. One run at one configuration establishes
nothing about whether ecological interaction generally increases or
decreases diversity.
"""

from __future__ import annotations

import argparse
import json

import numpy as np

from genevra.analysis.aggregation import permutation_test
from genevra.evolution.continuous import ContinuousEvolutionConfig, ContinuousEvolutionEngine
from genevra.evolution.engine import EvolutionConfig, EvolutionEngine
from genevra.evolution.fitness import SurvivalResourceFitness
from genevra.evolution.population import PopulationConfig
from genevra.evolution.reproduction import PopulationReproductionConfig
from genevra.evolution.selection import TournamentSelection
from genevra.metrics.diversity import genotypic_diversity
from genevra.organism.genome import ControllerArchitecture
from genevra.organism.learning import NoLearning
from genevra.organism.mutation import GaussianMutation
from genevra.organism.organism import OrganismConfig
from genevra.simulation.grid_world import GridWorldConfig
from genevra.simulation.shared_grid_world import SharedGridWorldConfig
from genevra.simulation.types import Action

VIEW_RADIUS = 1
MEMORY_SIZE = 4
POPULATION_SIZE = 12
GENERATIONS = 10
STEPS_PER_LIFETIME = 40
# Approximately matched total organism-lifetime-step budgets:
# isolated = population_size * generations * steps_per_lifetime
SHARED_TOTAL_STEPS = (POPULATION_SIZE * GENERATIONS * STEPS_PER_LIFETIME) // POPULATION_SIZE


def isolated_final_diversity(seed: int) -> float:
    grid_features = (2 * VIEW_RADIUS + 1) ** 2 * 2
    architecture = ControllerArchitecture(
        input_size=grid_features + 2 + MEMORY_SIZE, hidden_size=8, output_size=len(Action)
    )
    organism_config = OrganismConfig(
        view_radius=VIEW_RADIUS, memory_size=MEMORY_SIZE, initial_energy=30.0
    )
    population_config = PopulationConfig(
        size=POPULATION_SIZE, architecture=architecture, organism_config=organism_config
    )
    environment_config = GridWorldConfig(
        width=12, height=12, view_radius=VIEW_RADIUS, max_steps=STEPS_PER_LIFETIME
    )
    config = EvolutionConfig(
        generations=GENERATIONS,
        steps_per_lifetime=STEPS_PER_LIFETIME,
        environment_config=environment_config,
        population_config=population_config,
        fitness_function=SurvivalResourceFitness(),
        selection_strategy=TournamentSelection(tournament_size=3),
        reproduction=PopulationReproductionConfig(
            energy_threshold=3.0, mutation_operator=GaussianMutation()
        ),
        learning_rule_factory=NoLearning,
        seed=seed,
    )
    engine = EvolutionEngine(config)
    engine.run()
    genomes = engine.population.snapshot_genomes()
    return genotypic_diversity(genomes) if genomes else float("nan")


def shared_final_diversity(seed: int) -> float:
    grid_features = (2 * VIEW_RADIUS + 1) ** 2 * 3
    architecture = ControllerArchitecture(
        input_size=grid_features + 2 + MEMORY_SIZE, hidden_size=8, output_size=len(Action)
    )
    organism_config = OrganismConfig(
        view_radius=VIEW_RADIUS, memory_size=MEMORY_SIZE, initial_energy=30.0, channels=3
    )
    environment_config = SharedGridWorldConfig(
        width=12,
        height=12,
        view_radius=VIEW_RADIUS,
        max_agents=POPULATION_SIZE + 4,
        max_steps=1_000_000,
    )
    config = ContinuousEvolutionConfig(
        total_steps=SHARED_TOTAL_STEPS,
        initial_population=POPULATION_SIZE,
        max_population=POPULATION_SIZE + 4,
        environment_config=environment_config,
        architecture=architecture,
        organism_config=organism_config,
        reproduction_energy_threshold=3.0,
        offspring_energy_cost=2.0,
        seed=seed,
        log_every=50,
    )
    engine = ContinuousEvolutionEngine(config)
    engine.run()
    genomes = [living.genome for living in engine.population.values()]
    return genotypic_diversity(genomes) if genomes else float("nan")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seeds", type=int, nargs="+", default=[0, 1, 2, 3, 4])
    parser.add_argument("--output", type=str, default=None)
    args = parser.parse_args()

    isolated = [isolated_final_diversity(seed) for seed in args.seeds]
    shared = [shared_final_diversity(seed) for seed in args.seeds]

    print(f"seeds={args.seeds}")
    print(f"isolated final genotypic diversity: {[round(v, 3) for v in isolated]}")
    print(f"shared   final genotypic diversity: {[round(v, 3) for v in shared]}")

    test_result = permutation_test(
        isolated, shared, np.random.default_rng(0), num_permutations=2000
    )
    print(
        f"permutation test: observed_difference={test_result.observed_difference:.4f} "
        f"p_value={test_result.p_value:.4f} "
        "(descriptive infrastructure check, not a scientific conclusion)"
    )

    if args.output:
        with open(args.output, "w") as f:
            json.dump(
                {
                    "seeds": args.seeds,
                    "isolated_final_genotypic_diversity": isolated,
                    "shared_final_genotypic_diversity": shared,
                    "permutation_test": {
                        "observed_difference": test_result.observed_difference,
                        "p_value": test_result.p_value,
                        "num_permutations": test_result.num_permutations,
                    },
                },
                f,
                indent=2,
            )
        print(f"wrote {args.output}")


if __name__ == "__main__":
    main()
