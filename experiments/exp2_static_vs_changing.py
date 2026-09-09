"""EXPERIMENT 2: Static vs. Changing Environment.

Hypothesis: a resource-regeneration regime that changes partway through a
run (`RegimeChangeDynamics`) produces different novelty and diversity
trajectories than a fixed regime (`StaticDynamics`) at the same average
regeneration rate.

Independent variable: `GridWorldConfig.dynamics` — `StaticDynamics` at a
fixed resource_regen_prob vs. `RegimeChangeDynamics` switching from a low
to a high regeneration regime partway through the run (same population
size, generations, and average regeneration rate across the run).

Dependent measurements: per-generation `instantaneous_novelty`,
`genotypic_diversity`, and `behavioral_diversity` trajectories (read
directly from each condition's stored `GenerationSnapshot` trajectory).

Controlled variables: population size, controller architecture, organism
config, mutation operator, selection strategy, reproduction config,
generations, steps per lifetime, world size/obstacle/resource densities —
everything except `dynamics`. Seed sequence is shared across both
conditions via `ComparisonRunner`.

This is an infrastructure-validation experiment for GENEVRA's
`EnvironmentDynamics` abstraction and `ComparisonRunner`, not a claim that
environmental change generally increases or decreases novelty/diversity —
one small comparison at one configuration cannot establish that.
"""

from __future__ import annotations

import argparse
import json

from genevra.analysis.aggregation import aggregate_metric_across_runs
from genevra.analysis.comparison import ComparisonRunner
from genevra.evolution.engine import EvolutionConfig
from genevra.evolution.fitness import SurvivalResourceFitness
from genevra.evolution.population import PopulationConfig
from genevra.evolution.reproduction import PopulationReproductionConfig
from genevra.evolution.selection import TournamentSelection
from genevra.experiments.config import ExperimentConfig
from genevra.organism.genome import ControllerArchitecture
from genevra.organism.learning import NoLearning
from genevra.organism.mutation import GaussianMutation
from genevra.organism.organism import OrganismConfig
from genevra.simulation.dynamics import EnvironmentRegime, RegimeChangeDynamics, StaticDynamics
from genevra.simulation.grid_world import GridWorldConfig
from genevra.simulation.types import Action

VIEW_RADIUS = 1
MEMORY_SIZE = 4
_GRID_FEATURES = (2 * VIEW_RADIUS + 1) ** 2 * 2
INPUT_SIZE = _GRID_FEATURES + 2 + MEMORY_SIZE
GENERATIONS = 12
STEPS_PER_LIFETIME = 60


def _base_evolution_config(seed: int, environment_config: GridWorldConfig) -> EvolutionConfig:
    architecture = ControllerArchitecture(
        input_size=INPUT_SIZE, hidden_size=8, output_size=len(Action)
    )
    organism_config = OrganismConfig(
        view_radius=VIEW_RADIUS, memory_size=MEMORY_SIZE, initial_energy=25.0
    )
    population_config = PopulationConfig(
        size=16, architecture=architecture, organism_config=organism_config
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


def static_condition(seed: int) -> ExperimentConfig:
    dynamics = StaticDynamics(EnvironmentRegime(resource_regen_prob=0.03))
    env = GridWorldConfig(
        width=14,
        height=14,
        view_radius=VIEW_RADIUS,
        max_steps=STEPS_PER_LIFETIME,
        dynamics=dynamics,
    )
    return ExperimentConfig(name="static", evolution=_base_evolution_config(seed, env))


def changing_condition(seed: int) -> ExperimentConfig:
    dynamics = RegimeChangeDynamics(
        regime_before=EnvironmentRegime(resource_regen_prob=0.005),
        regime_after=EnvironmentRegime(resource_regen_prob=0.055),
        switch_step=STEPS_PER_LIFETIME // 2,
    )
    env = GridWorldConfig(
        width=14,
        height=14,
        view_radius=VIEW_RADIUS,
        max_steps=STEPS_PER_LIFETIME,
        dynamics=dynamics,
    )
    return ExperimentConfig(name="changing", evolution=_base_evolution_config(seed, env))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seeds", type=int, nargs="+", default=[0, 1, 2, 3, 4])
    parser.add_argument("--output", type=str, default=None)
    args = parser.parse_args()

    runner = ComparisonRunner(
        conditions={"static": static_condition, "changing": changing_condition}, seeds=args.seeds
    )
    result = runner.run()

    print(f"seeds={result.seeds}")
    print(f"failures={result.failures()}")

    for metric in ("instantaneous_novelty", "genotypic_diversity", "behavioral_diversity"):
        for condition_name, results in result.conditions.items():
            trajectories = [r["trajectory"] for r in results]
            aggregates = aggregate_metric_across_runs(trajectories, lambda g, m=metric: g[m])
            if aggregates:
                final = aggregates[-1]
                print(
                    f"{metric} [{condition_name}]: final generation mean={final.mean:.3f} "
                    f"(n_runs={final.n_runs}, percentile_range=[{final.percentile_low:.3f}, "
                    f"{final.percentile_high:.3f}])"
                )

    if args.output:
        with open(args.output, "w") as f:
            json.dump(result.conditions, f, indent=2)
        print(f"wrote {args.output}")


if __name__ == "__main__":
    main()
