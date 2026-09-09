"""EXPERIMENT 3: Fixed vs. Heritable Mutation Strength.

Hypothesis: allowing mutation rate/sigma to itself mutate and be
inherited (the default in `GaussianMutation` — see `docs/organism.md`)
produces different evolutionary dynamics (mean heritable mutation
rate/sigma over generations, genotypic diversity) than fixing mutation
strength at a constant value for the whole population.

Independent variable: whether `genome.mutation_genes` are allowed to
drift. "Heritable" uses `GaussianMutation` as-is (mutation_genes mutate at
GaussianMutation's own small meta-rate — see
`genevra.organism.mutation`). "Fixed" uses `FixedRateMutation`, a
condition-local wrapper defined in this script that mutates
`controller_weights`/`metabolic_genes`/`learning_genes` exactly like
`GaussianMutation` but always resets `mutation_genes` back to the
population's initial `(rate, sigma)` after mutating — so mutation
strength can never drift from its starting value.

Dependent measurements: `mean_mutation_rate`/`mean_mutation_sigma` and
`genotypic_diversity` trajectories.

Controlled variables: everything else — population size, controller
architecture, organism config, selection strategy, reproduction config,
generations, steps per lifetime, environment. Seed sequence shared across
conditions via `ComparisonRunner`.

Infrastructure-validation experiment: demonstrates that
`genevra.organism.mutation.MutationOperator` is genuinely swappable at the
population level and that heritable vs. fixed mutation strength produce
measurably different `mean_mutation_rate`/`mean_mutation_sigma`
trajectories — not a claim about which is "better" for open-ended
evolution in general.
"""

from __future__ import annotations

import argparse
import json

import numpy as np

from genevra.analysis.comparison import ComparisonRunner
from genevra.evolution.engine import EvolutionConfig
from genevra.evolution.fitness import SurvivalResourceFitness
from genevra.evolution.population import PopulationConfig
from genevra.evolution.reproduction import PopulationReproductionConfig
from genevra.evolution.selection import TournamentSelection
from genevra.experiments.config import ExperimentConfig
from genevra.organism.genome import ControllerArchitecture, Genome
from genevra.organism.learning import NoLearning
from genevra.organism.mutation import GaussianMutation
from genevra.organism.organism import OrganismConfig
from genevra.simulation.grid_world import GridWorldConfig
from genevra.simulation.types import Action

VIEW_RADIUS = 1
MEMORY_SIZE = 4
_GRID_FEATURES = (2 * VIEW_RADIUS + 1) ** 2 * 2
INPUT_SIZE = _GRID_FEATURES + 2 + MEMORY_SIZE
GENERATIONS = 15
STEPS_PER_LIFETIME = 50
INITIAL_RATE = 0.15
INITIAL_SIGMA = 0.2


class FixedRateMutation:
    """Mutates like `GaussianMutation`, but pins `mutation_genes` back to
    `(INITIAL_RATE, INITIAL_SIGMA)` after every mutation — the population's
    heritable mutation strength can never drift from its starting value."""

    def __init__(self) -> None:
        self._inner = GaussianMutation()

    def mutate(self, genome: Genome, rng: np.random.Generator) -> Genome:
        mutated = self._inner.mutate(genome, rng)
        mutated.mutation_genes[:] = [INITIAL_RATE, INITIAL_SIGMA]
        return mutated


def _base_evolution_config(seed: int, mutation_operator) -> EvolutionConfig:
    architecture = ControllerArchitecture(
        input_size=INPUT_SIZE, hidden_size=8, output_size=len(Action)
    )
    organism_config = OrganismConfig(
        view_radius=VIEW_RADIUS, memory_size=MEMORY_SIZE, initial_energy=25.0
    )
    population_config = PopulationConfig(
        size=16,
        architecture=architecture,
        organism_config=organism_config,
        initial_mutation_rate=INITIAL_RATE,
        initial_mutation_sigma=INITIAL_SIGMA,
    )
    environment_config = GridWorldConfig(
        width=14, height=14, view_radius=VIEW_RADIUS, max_steps=STEPS_PER_LIFETIME
    )
    return EvolutionConfig(
        generations=GENERATIONS,
        steps_per_lifetime=STEPS_PER_LIFETIME,
        environment_config=environment_config,
        population_config=population_config,
        fitness_function=SurvivalResourceFitness(),
        selection_strategy=TournamentSelection(tournament_size=3),
        reproduction=PopulationReproductionConfig(
            energy_threshold=2.0, mutation_operator=mutation_operator
        ),
        learning_rule_factory=NoLearning,
        seed=seed,
    )


def fixed_condition(seed: int) -> ExperimentConfig:
    return ExperimentConfig(
        name="fixed", evolution=_base_evolution_config(seed, FixedRateMutation())
    )


def heritable_condition(seed: int) -> ExperimentConfig:
    return ExperimentConfig(
        name="heritable", evolution=_base_evolution_config(seed, GaussianMutation())
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seeds", type=int, nargs="+", default=[0, 1, 2, 3, 4])
    parser.add_argument("--output", type=str, default=None)
    args = parser.parse_args()

    runner = ComparisonRunner(
        conditions={"fixed": fixed_condition, "heritable": heritable_condition}, seeds=args.seeds
    )
    result = runner.run()

    print(f"seeds={result.seeds}")
    print(f"failures={result.failures()}")

    for condition_name, results in result.conditions.items():
        final_rates = [
            r["trajectory"][-1]["mean_mutation_rate"] for r in results if r["trajectory"]
        ]
        final_sigmas = [
            r["trajectory"][-1]["mean_mutation_sigma"] for r in results if r["trajectory"]
        ]
        final_diversity = [
            r["trajectory"][-1]["genotypic_diversity"] for r in results if r["trajectory"]
        ]
        print(
            f"[{condition_name}] final mean_mutation_rate={np.mean(final_rates):.4f} "
            f"final mean_mutation_sigma={np.mean(final_sigmas):.4f} "
            f"final genotypic_diversity={np.mean(final_diversity):.4f}"
        )

    if args.output:
        with open(args.output, "w") as f:
            json.dump(result.conditions, f, indent=2)
        print(f"wrote {args.output}")


if __name__ == "__main__":
    main()
