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

**Foundation stage.** This repository currently contains project
scaffolding, tooling, and reproducibility utilities only:

- `genevra.utils.seeding` — deterministic seeding of stdlib `random` and a
  `numpy.random.Generator`, so runs are replayable from a seed.
- `genevra.utils.logging` — consistent experiment logging setup.

No simulation, organism, learning, evolution, metrics, or experiment code
exists yet. See [`docs/architecture.md`](docs/architecture.md) for the
intended module layout and the reasoning behind it. Each layer will be
built and validated incrementally, in its own change, before the next one
is added — not assembled all at once.

## High-level architecture

```
src/genevra/
  simulation/   environment dynamics, sensors, actions        (planned)
  organism/     genome, small NN controller, memory, dev.     (planned)
  learning/     within-lifetime learning mechanisms            (planned)
  evolution/    selection, mutation, recombination operators   (planned)
  metrics/      fitness, novelty, diversity, evolvability      (planned)
  experiments/  config-driven orchestration of a run           (planned)
  analysis/     post-hoc comparison across runs/conditions      (planned)
  utils/        seeding, logging                                (done)
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

There is no experiment to run yet — see Development Status above.

## How experiments will be organized

Once the core modules exist, an experiment will be: a YAML/TOML config
under `configs/` describing the environment, population, mutation/learning
setup, and seed; a small entry-point script under `experiments/` that loads
the config, builds the run via `genevra.experiments`, and writes
trajectories, metrics, and logs to `results/<run-id>/`; and, optionally, a
notebook under `notebooks/` for exploratory analysis of those outputs.
Comparing evolutionary conditions means running the same config with
different parameter overrides and seeds, then comparing their metrics —
not writing a new one-off script per comparison.

## License

MIT — see [LICENSE](LICENSE).
