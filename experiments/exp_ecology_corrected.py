"""RQ4 CORRECTION: same-engine ecological competition comparison.

The original RQ4 (`exp1_isolated_vs_shared.py`) compared
`EvolutionEngine`+`GridWorld` against `ContinuousEvolutionEngine`+
`SharedGridWorld` — two different engines (discrete vs. continuous
generations, tournament selection vs. birth/death, `channels=2` vs. `3`).
An independent audit found this confounds engine architecture with
ecology and downgraded the result to CONFOUNDED (see
`research_evidence/research_questions/RQ4.json`).

This experiment holds the engine, `SharedGridWorldConfig`,
`ContinuousEvolutionConfig`, controller architecture, organism config,
and metric IDENTICAL across both conditions and varies only
`resource_a_density` (per `genevra.ecology.competition`'s own docstring:
"resource_a_density and max_agents set competition strength"):

- `minimal_competition`: resource_a_density=0.30 (abundant resource A)
- `shared_competition`: resource_a_density=0.05 (scarce resource A)

Everything else — `resource_b_density`, `max_agents`, `total_steps`,
`initial_population`, architecture, mutation, reproduction thresholds,
the seed sequence — is identical between conditions.

Primary metric: final-population genotypic diversity (matches the
original RQ4's metric, for comparability). Secondary/exploratory:
final population size and mean energy (already tracked by
`ContinuousEvolutionEngine`, no new instrumentation).
"""

from __future__ import annotations

import argparse
import json

from genevra.evolution.continuous import ContinuousEvolutionConfig, ContinuousEvolutionEngine
from genevra.metrics.diversity import genotypic_diversity
from genevra.organism.genome import ControllerArchitecture
from genevra.organism.organism import OrganismConfig
from genevra.simulation.shared_grid_world import SharedGridWorldConfig
from genevra.simulation.types import Action

VIEW_RADIUS = 1
MEMORY_SIZE = 4
POPULATION_SIZE = 12
TOTAL_STEPS = 400


def _run(seed: int, resource_a_density: float) -> dict[str, float]:
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
        resource_a_density=resource_a_density,
    )
    config = ContinuousEvolutionConfig(
        total_steps=TOTAL_STEPS,
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
    living = list(engine.population.values())
    genomes = [ind.genome for ind in living]
    return {
        "genotypic_diversity": genotypic_diversity(genomes) if genomes else float("nan"),
        "final_population_size": float(len(living)),
        "mean_energy": (
            float(sum(ind.organism.metabolism.energy for ind in living) / len(living))
            if living
            else float("nan")
        ),
    }


def minimal_competition(seed: int) -> dict[str, float]:
    return _run(seed, resource_a_density=0.30)


def shared_competition(seed: int) -> dict[str, float]:
    return _run(seed, resource_a_density=0.05)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seeds", type=int, nargs="+", default=[0, 1, 2, 3])
    parser.add_argument("--output", type=str, default=None)
    args = parser.parse_args()

    minimal = [minimal_competition(seed) for seed in args.seeds]
    shared = [shared_competition(seed) for seed in args.seeds]

    minimal_diversity = [round(r["genotypic_diversity"], 3) for r in minimal]
    shared_diversity = [round(r["genotypic_diversity"], 3) for r in shared]
    print(f"seeds={args.seeds}")
    print(f"minimal_competition genotypic_diversity: {minimal_diversity}")
    print(f"shared_competition  genotypic_diversity: {shared_diversity}")

    if args.output:
        with open(args.output, "w") as f:
            json.dump(
                {"seeds": args.seeds, "minimal_competition": minimal, "shared_competition": shared},
                f,
                indent=2,
            )


if __name__ == "__main__":
    main()
