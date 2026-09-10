"""Phase 7.1: reproduce GENEVRA's performance profile.

Two complementary measurements:

1. A `cProfile` run over a representative `EvolutionEngine` (isolated,
   single-organism-per-episode) and `SharedGridWorld` multi-agent loop,
   reported as cumulative time by function — this is what tells us
   whether `_extract_local_grid`/`np.pad` really is ~64% of shared-world
   runtime, rather than assuming it.
2. Targeted microbenchmarks (`time.perf_counter`, averaged over repeated
   calls) for the specific operations Phase 7 optimizes, so before/after
   comparisons aren't confounded by everything else a full run does.

This script is a measurement tool, not a test: its numbers are specific
to the machine it runs on and are not asserted anywhere. Run it before
and after an optimization and compare the printed tables.
"""

from __future__ import annotations

import cProfile
import io
import pstats
import time
from collections.abc import Callable

import numpy as np

from genevra.evolution.engine import EvolutionConfig, EvolutionEngine
from genevra.evolution.fitness import SurvivalResourceFitness
from genevra.evolution.population import PopulationConfig
from genevra.evolution.reproduction import PopulationReproductionConfig
from genevra.evolution.selection import TournamentSelection
from genevra.organism.genome import ControllerArchitecture
from genevra.organism.mutation import GaussianMutation
from genevra.organism.organism import OrganismConfig
from genevra.simulation.grid_world import GridWorld, GridWorldConfig
from genevra.simulation.shared_grid_world import SharedGridWorld, SharedGridWorldConfig
from genevra.simulation.types import Action


def _time_it(fn: Callable[[], object], repeats: int) -> float:
    fn()  # warm-up: exclude first-call effects (allocation, cache) from the measurement
    start = time.perf_counter()
    for _ in range(repeats):
        fn()
    return (time.perf_counter() - start) / repeats


def microbenchmark_extract_local_grid(width: int, height: int, repeats: int = 2000) -> None:
    world = GridWorld(GridWorldConfig(width=width, height=height, view_radius=2))
    world.reset(seed=0)
    per_call = _time_it(world._extract_local_grid, repeats)
    print(f"  GridWorld._extract_local_grid  ({width}x{height}): {per_call * 1e6:8.2f} us/call")


def microbenchmark_shared_extract_local_grid(
    width: int, height: int, num_agents: int, repeats: int = 500
) -> None:
    world = SharedGridWorld(SharedGridWorldConfig(width=width, height=height, view_radius=2))
    world.reset(seed=0)
    for agent_id in range(num_agents):
        world.add_agent(agent_id)

    def extract_all() -> None:
        for agent_id in world.agent_ids:
            world._extract_local_grid(world._agent_positions[agent_id])

    per_call = _time_it(extract_all, repeats)
    print(
        f"  SharedGridWorld extract-all-agents ({width}x{height}, {num_agents} agents): "
        f"{per_call * 1e6:8.2f} us/call"
    )


def _bench_one_population_size(
    n: int, architecture: ControllerArchitecture, rng: np.random.Generator
) -> None:
    from genevra.organism.controller import Controller, batch_hidden
    from genevra.organism.genome import Genome

    genomes = [Genome.random(architecture, rng) for _ in range(n)]
    controllers = [Controller.from_weights(architecture, g.controller_weights) for g in genomes]
    inputs = rng.normal(0, 1, (n, architecture.input_size)).astype(np.float32)

    def individual() -> None:
        for controller, x in zip(controllers, inputs, strict=True):
            controller.hidden(x)

    def batched() -> None:
        batch_hidden(controllers, inputs)

    per_call_individual = _time_it(individual, 30)
    per_call_batched = _time_it(batched, 30)
    speedup = per_call_individual / per_call_batched if per_call_batched else float("inf")
    print(
        f"  N={n:5d}  individual: {per_call_individual * 1e6:9.2f} us  "
        f"batched: {per_call_batched * 1e6:9.2f} us  speedup: {speedup:5.2f}x"
    )


def microbenchmark_controller_inference(
    population_sizes: tuple[int, ...] = (10, 50, 200, 1000),
) -> None:
    architecture = ControllerArchitecture(input_size=52, hidden_size=16, output_size=len(Action))
    rng = np.random.default_rng(0)
    for n in population_sizes:
        _bench_one_population_size(n, architecture, rng)


def profile_isolated_engine(generations: int = 3, population_size: int = 40) -> None:
    architecture = ControllerArchitecture(input_size=56, hidden_size=16, output_size=len(Action))
    config = EvolutionConfig(
        generations=generations,
        steps_per_lifetime=80,
        environment_config=GridWorldConfig(width=25, height=25, view_radius=2, max_steps=80),
        population_config=PopulationConfig(
            size=population_size,
            architecture=architecture,
            organism_config=OrganismConfig(view_radius=2, memory_size=4, initial_energy=20.0),
        ),
        fitness_function=SurvivalResourceFitness(),
        selection_strategy=TournamentSelection(),
        reproduction=PopulationReproductionConfig(
            energy_threshold=-1e9, mutation_operator=GaussianMutation()
        ),
        seed=0,
    )
    profiler = cProfile.Profile()
    profiler.enable()
    EvolutionEngine(config).run()
    profiler.disable()

    stream = io.StringIO()
    stats = pstats.Stats(profiler, stream=stream).sort_stats("cumulative")
    stats.print_stats(15)
    print(stream.getvalue())


def profile_shared_world_stepping(steps: int = 300, num_agents: int = 20) -> None:
    world = SharedGridWorld(SharedGridWorldConfig(width=30, height=30, view_radius=2))
    world.reset(seed=0)
    for agent_id in range(num_agents):
        world.add_agent(agent_id)
    rng = np.random.default_rng(0)
    moves = [a for a in Action]

    profiler = cProfile.Profile()
    profiler.enable()
    for _ in range(steps):
        actions = {agent_id: moves[rng.integers(0, len(moves))] for agent_id in world.agent_ids}
        world.step(actions)
    profiler.disable()

    stream = io.StringIO()
    stats = pstats.Stats(profiler, stream=stream).sort_stats("cumulative")
    stats.print_stats(15)
    print(stream.getvalue())


if __name__ == "__main__":
    print("=== Microbenchmarks ===")
    microbenchmark_extract_local_grid(width=25, height=25)
    microbenchmark_extract_local_grid(width=100, height=100)
    microbenchmark_shared_extract_local_grid(width=30, height=30, num_agents=20)
    microbenchmark_shared_extract_local_grid(width=100, height=100, num_agents=20)
    microbenchmark_controller_inference()

    print("\n=== cProfile: isolated EvolutionEngine (3 generations, pop=40) ===")
    profile_isolated_engine()

    print("\n=== cProfile: SharedGridWorld stepping (300 steps, 20 agents) ===")
    profile_shared_world_stepping()
