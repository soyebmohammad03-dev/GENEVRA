# GENEVRA

GENEVRA is a research laboratory for studying **open-ended evolution,
evolvability, and adaptive intelligence** in small, neural-network-based
digital organisms — designed to run on a laptop, not a GPU cluster.

It is not a chatbot, not a RAG app, not an agent framework, and not another
"watch shapes evolve" artificial-life toy. It is a system for running
controlled evolutionary experiments and measuring what happens.

## Research motivation

Most evolutionary/artificial-life demos evolve a fixed behavior against a
fixed fitness function and stop. The more interesting — and much less
settled — questions are about the evolutionary *process* itself:

1. Can artificial organisms evolve not just better behaviors, but better
   **ways of learning**?
2. Can **evolvability itself** become an evolving, heritable property,
   rather than a fixed side effect of the representation?
3. Under what conditions does an evolving population keep producing
   genuinely novel behavior, instead of converging and stagnating?
4. How do mutation, learning, memory, exploration, recombination,
   environmental change, and ecological interaction jointly affect
   long-term evolutionary innovation?
5. Can evolutionary stagnation or an impending dead-end be **detected
   before it happens**, rather than diagnosed in hindsight?

These are framed as open research questions GENEVRA is built to
*investigate*, not as problems it claims to have solved. Where the
literature has partial answers (e.g. on evolvability, novelty search,
open-endedness), GENEVRA aims to be a platform for testing hypotheses
against those ideas empirically, on small, cheap, reproducible runs.

## What makes GENEVRA different

- **A laboratory, not one experiment.** Simulation, evolution, learning,
  metrics, and experiment orchestration are separate modules with explicit
  interfaces, so evolutionary conditions can be swapped and compared rather
  than hardcoded.
- **Evolvability as a variable, not a constant.** The learning/evolutionary
  mechanisms an organism uses are themselves heritable and mutable where
  appropriate — the question "can evolvability evolve?" needs that to be
  possible in the representation, not bolted on afterward.
- **Reproducibility first.** Every run is seed-driven and config-driven;
  the same config + seed must produce the same trajectory.
- **Laptop feasibility as a constraint, not an afterthought.** Small
  networks, vectorized NumPy simulation, and CPU parallelism where it
  helps — GPU acceleration is optional, never assumed.
- **Measurement built in.** Fitness alone doesn't answer these questions;
  novelty, diversity, and evolvability need their own first-class metrics
  and stagnation detectors, computed from — but decoupled from — the
  simulation and evolution code.

## Development status

**Experimental research platform — Phase 1–4 complete.** GENEVRA can now
run config-driven, reproducible evolutionary experiments end to end — a
population of small-neural-network organisms living, reproducing,
mutating, and being measured across generations — though only at the
small scales and single baseline experiment described below, not yet as a
validated tool for answering any of the research questions above:

- `genevra.utils` — reproducible seeding, experiment logging.
- `genevra.simulation` — the `Environment` protocol, a `VectorEnvironment`
  batch wrapper, and `GridWorld`: a configurable 2D world with obstacles,
  regenerating resources, and a strict boundary between what an organism
  can sense (`Observation`, an egocentric local window) and
  simulator-internal state (position, step count, RNG state — reachable
  only via `snapshot()`/`restore()`, for replay and checkpointing). See
  [`docs/environment.md`](docs/environment.md).
- `genevra.organism` — a small NumPy neural controller, genome/phenotype
  separation, sensing, short-term memory, metabolism (heritable action
  costs), a mutation operator whose rate/step-size are themselves
  heritable genes, and a minimal but structurally real within-lifetime
  learning mechanism (Hebbian plasticity on the output layer) kept
  distinct from both inherited weights and the heritable parameters that
  control how learning happens. See [`docs/organism.md`](docs/organism.md).
- `genevra.evolution` — a population of many organisms evolving over
  discrete generations: configurable selection (fitness-proportional,
  tournament, elitist), population-level reproduction with an explicit
  reproduction-eligibility rule, and compact per-individual lineage
  tracking (ancestry, birth/death generation, genome-hash identity). See
  [`docs/architecture.md`](docs/architecture.md#the-populationevolution-layer).
- `genevra.metrics` — fitness summaries; genotypic diversity (genome
  distance) kept structurally separate from behavioral diversity
  (behavior-signature distance); a persistent novelty archive that is
  demonstrably not fitness under another name; and an operational,
  mutation-neighborhood `EvolvabilityAnalyzer` that measures mutational
  variation, explicitly documented as distinct from adaptive success. See
  [`docs/metrics.md`](docs/metrics.md).
- `genevra.experiments` — `ExperimentConfig`/`ExperimentRunner` producing
  a self-contained, JSON-serializable `ExperimentResult`; same config +
  same seed reproduces byte-identical results (verified in
  `tests/test_experiments.py` and by running
  [`experiments/baseline.py`](experiments/baseline.py) twice). See
  [`docs/experiments.md`](docs/experiments.md).

Not yet implemented: `genevra.analysis` (post-hoc cross-run comparison,
automated hypothesis discovery), overlapping generations, sexual
reproduction/recombination, ecological interaction between organisms
sharing one environment, speciation, and migration between environments.
See [`docs/architecture.md`](docs/architecture.md) for the full module
layout and what's planned versus implemented. Each layer is built and
validated incrementally, not assembled all at once — this is an
experimental research platform, not a demonstration that any of GENEVRA's
research questions have been answered; the one baseline experiment that
exists (24 organisms, 15 generations, one environment configuration) is a
pipeline demonstration, not a scientific result.

## High-level architecture

```
src/genevra/
  simulation/   Environment protocol, VectorEnvironment, GridWorld  (done)
  organism/     genome, phenotype, controller, sensors, memory,
                learning, metabolism, mutation, reproduction        (done)
  evolution/    population, selection, reproduction, lineage,
                the generational EvolutionEngine                    (done)
  metrics/      fitness, genotypic/behavioral diversity, novelty,
                evolvability, structured trajectories               (done)
  experiments/  config-driven orchestration + ExperimentResult      (done)
  analysis/     post-hoc comparison across runs/conditions          (planned)
  utils/        seeding, logging                                   (done)
  arrays/       shared NumPy array type aliases                    (done)
```

Full rationale for this split is in [`docs/architecture.md`](docs/architecture.md).

## Reproducibility philosophy

- Every stochastic experiment is driven by an explicit integer seed via
  `genevra.utils.seeding.seed_everything`, which returns a
  `numpy.random.Generator` — GENEVRA code threads this generator through
  rather than relying on hidden global RNG state.
- Experiment parameters live in versioned config files under `configs/`
  (once the first real experiment defines their schema), not hardcoded in
  scripts, so a run is fully specified by `(config, seed)`.
- Experiment outputs are written under `results/<run-id>/` and are
  git-ignored — results are regenerated from `(config, seed)`, not
  committed as artifacts.

## Install and run

Requires Python >= 3.11.

```bash
# using uv (recommended)
uv venv
uv pip install -e ".[dev]"

# or plain pip
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
```

Run the test suite:

```bash
pytest
ruff check .
mypy
```

Run the baseline evolutionary experiment:

```bash
PYTHONPATH=src python experiments/baseline.py --seed 0
PYTHONPATH=src python experiments/baseline.py --seed 0 --output results/baseline_seed0.json
```

## How experiments are organized

An experiment is an `ExperimentConfig` (`genevra.experiments.config`) — a
name plus an `EvolutionConfig` describing the environment, population,
organism, mutation/learning, fitness, selection, and reproduction setup,
and a seed — run via `ExperimentRunner.run()`
(`genevra.experiments.runner`), which returns a self-contained,
JSON-serializable `ExperimentResult`. Configuration is currently Python
dataclasses rather than a YAML/TOML file format — see
[`docs/experiments.md`](docs/experiments.md) for why, and what a
file-based loader would need to add. `experiments/baseline.py` is a
runnable entry-point script that builds a config, runs it, and prints/
optionally writes the result; comparing evolutionary conditions means
building two `ExperimentConfig`s that differ in exactly the variable under
test and running each across the same seeds — infrastructure this phase
establishes, not yet a comparison *runner*, and not yet a notebook-based
exploratory workflow under `notebooks/`.

## License

MIT — see [LICENSE](LICENSE).
