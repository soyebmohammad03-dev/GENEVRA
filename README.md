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

**Experimental research platform — Phase 1–6 complete.** GENEVRA now runs
config-driven, reproducible evolutionary experiments end to end — isolated
or ecologically shared, static or temporally dynamic — and can aggregate,
compare, and analyze the results, though only at the small scales and
handful of infrastructure-validation experiments described below, not yet
as a validated tool for answering any of the research questions above (see
[`docs/research_questions.md`](docs/research_questions.md) for that
distinction, spelled out explicitly):

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
  either discrete non-overlapping generations (`EvolutionEngine`:
  configurable selection — fitness-proportional, tournament, elitist —
  population-level reproduction with an explicit reproduction-eligibility
  rule) or overlapping generations in one shared world
  (`ContinuousEvolutionEngine`: organism age, per-tick birth/death,
  bounded population size), plus compact per-individual lineage tracking
  (ancestry, birth/death generation, genome-hash identity) shared by
  both. See
  [`docs/architecture.md`](docs/architecture.md#the-populationevolution-layer)
  and [`docs/ecology.md`](docs/ecology.md).
- `genevra.simulation` also includes `SharedGridWorld` (multiple
  organisms coexisting, two resource types, deterministic spatial
  competition via `InteractionSystem`) and `EnvironmentDynamics`
  (static/periodic/regime-change/stochastic resource regeneration,
  usable by both `GridWorld` and `SharedGridWorld`, fully reproducible
  from a seed). See [`docs/ecology.md`](docs/ecology.md).
- `genevra.metrics` — fitness summaries; genotypic diversity (genome
  distance) kept structurally separate from behavioral diversity
  (behavior-signature distance); cumulative *and* instantaneous novelty
  (never conflated with fitness); and an operational, mutation-
  neighborhood `EvolvabilityAnalyzer` that measures mutational variation,
  explicitly documented as distinct from adaptive success. See
  [`docs/metrics.md`](docs/metrics.md).
- `genevra.experiments` — `ExperimentConfig`/`ExperimentRunner` producing
  a self-contained, JSON-serializable `ExperimentResult` (now also
  carrying environment summary, condition id, and explicit failure
  information for runs that raised); same config + same seed reproduces
  byte-identical results (verified in `tests/test_experiments.py` and by
  running [`experiments/baseline.py`](experiments/baseline.py) twice).
  See [`docs/experiments.md`](docs/experiments.md).
- `genevra.analysis` — multi-seed/multi-condition aggregation with a real
  (non-fabricated) non-parametric permutation test; `ComparisonRunner` for
  controlled comparisons sharing a seed sequence across conditions; an
  evolutionary `StagnationAnalyzer` that structurally never equates a
  fitness plateau with stagnation; lineage analysis; and
  evolvability-over-time sampling. See [`docs/analysis.md`](docs/analysis.md).
- `genevra.visualization` and `genevra.cli` — reproducible plots from
  stored results (`pip install -e ".[viz]"`) and a `genevra run|analyze|
  inspect|compare` command-line entry point.

Not yet implemented: automated hypothesis discovery, sexual reproduction/
recombination, speciation, migration between environments, and hazard/
predation/communication/cooperation interaction mechanisms (the
`InteractionSystem`/`EnvironmentDynamics` protocols support adding these
later without redesign). See [`docs/architecture.md`](docs/architecture.md)
for the full module layout. Each layer is built and validated
incrementally, not assembled all at once — this is an experimental
research platform, not a demonstration that any of GENEVRA's research
questions have been answered; the baseline and three controlled-comparison
experiments that exist are pipeline demonstrations (a handful of seeds,
small populations, short runs), not scientific results — see
[`docs/research_questions.md`](docs/research_questions.md) for exactly
what would be needed to go further.

## Literature reproduction and open-endedness lab (Phase 11 + 12)

`genevra.literature` and `genevra.innovation` add a layer for testing
whether published evolutionary claims hold under GENEVRA's own model
assumptions (`genevra reproduce`, `genevra falsify`), and a
multi-dimensional open-endedness/innovation diagnostic framework built on
GENEVRA's lineage and strategy machinery (`genevra open-endedness`,
`genevra innovation`, `genevra activity`). See
[`docs/research_reproduction.md`](docs/research_reproduction.md),
[`docs/falsification.md`](docs/falsification.md),
[`docs/open_endedness.md`](docs/open_endedness.md),
[`docs/innovation.md`](docs/innovation.md), and the "Phase 11 + 12"
section of [`docs/research_questions.md`](docs/research_questions.md) for
what is established vs. exploratory.

## Evolutionary mechanisms and research artifact lab (Phase 13 + 14)

`genevra.mechanisms` decomposes evolvability into independently-measured
traits — robustness, plasticity cost, generalization, mutational
landscape, learning-strategy evolution, regime classification, and a
causal-chain scaffold (`genevra robustness`, `genevra generalization`,
`genevra analyze-mechanisms`) — and `genevra.artifacts` generates
publication-style figures, tables, and a structured, provenance-linked
`research_artifacts/<experiment_id>/` directory from stored GENEVRA data
(`genevra figures`, `genevra tables`, `genevra artifacts`,
`genevra report`). See
[`docs/evolutionary_mechanisms.md`](docs/evolutionary_mechanisms.md),
[`docs/robustness_plasticity_evolvability.md`](docs/robustness_plasticity_evolvability.md),
[`docs/generalization.md`](docs/generalization.md),
[`docs/figure_system.md`](docs/figure_system.md),
[`docs/research_artifacts.md`](docs/research_artifacts.md), and the
"Phase 13 + 14" section of
[`docs/research_questions.md`](docs/research_questions.md) for what is
established vs. exploratory.

## High-level architecture

```
src/genevra/
  simulation/     Environment protocol, VectorEnvironment, GridWorld,
                  SharedGridWorld, EnvironmentDynamics, InteractionSystem (done)
  organism/       genome, phenotype, controller, sensors, memory,
                  learning, metabolism, mutation, reproduction           (done)
  evolution/      population, selection, reproduction, lineage,
                  EvolutionEngine (discrete) + ContinuousEvolutionEngine
                  (overlapping generations)                              (done)
  metrics/        fitness, genotypic/behavioral diversity, novelty
                  (cumulative + instantaneous), evolvability,
                  structured trajectories                                (done)
  experiments/    config-driven orchestration + ExperimentResult          (done)
  analysis/       aggregation, ComparisonRunner, StagnationAnalyzer,
                  lineage analysis, evolvability-over-time                (done)
  visualization/  reproducible plots from stored results (optional dep)   (done)
  cli/            `genevra run|analyze|inspect|compare`                   (done)
  utils/          seeding, logging                                       (done)
  arrays/         shared NumPy array type aliases                        (done)
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
uv pip install -e ".[viz]"   # optional: matplotlib, for genevra.visualization

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

Run the baseline evolutionary experiment, or the `genevra` CLI:

```bash
PYTHONPATH=src python experiments/baseline.py --seed 0
PYTHONPATH=src python experiments/baseline.py --seed 0 --output results/baseline_seed0.json

genevra run --seed 0 --output results/baseline_seed0.json
genevra inspect results/baseline_seed0.json
genevra analyze results/baseline_seed0.json    # stagnation report
genevra compare                                # lists the controlled experiments below
```

Run one of the three controlled comparison experiments:

```bash
PYTHONPATH=src python experiments/exp1_isolated_vs_shared.py --seeds 0 1 2 3 4
PYTHONPATH=src python experiments/exp2_static_vs_changing.py --seeds 0 1 2 3 4
PYTHONPATH=src python experiments/exp3_fixed_vs_heritable_mutation.py --seeds 0 1 2 3 4
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
optionally writes the result. Comparing evolutionary conditions uses
`genevra.analysis.comparison.ComparisonRunner`, which runs the same seed
list across two or more named `ExperimentConfig`-producing factories and
returns every run's result grouped by condition — see
[`docs/analysis.md`](docs/analysis.md) and the three scripts above for
worked examples. A notebook-based exploratory workflow under `notebooks/`
does not exist yet.

## License

MIT — see [LICENSE](LICENSE).
