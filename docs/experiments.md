# Experiment Configuration and Orchestration

Module: `genevra.experiments` (`config.py`, `runner.py`, `result.py`);
runnable entry point: `experiments/baseline.py`.

## Configuration is Python dataclasses, not a file format

An `ExperimentConfig` is a name plus an `EvolutionConfig` (see
`docs/architecture.md`), itself composed of an environment config
(`GridWorldConfig`), a population config (`PopulationConfig`, which
carries the organism/controller config), a fitness function, a selection
strategy, a reproduction config (energy threshold + mutation operator), a
learning rule factory, and a seed. All of it is Python objects — there is
no YAML/TOML file loader or schema validator in this codebase yet.

This is a deliberate scope choice, not an oversight: the requirement is
"same config + same seed = reproducible experiment," which typed
dataclasses satisfy directly (and with static type checking, via
`mypy --strict`), without first building a config-file format, a parser,
and a schema validator for a single-user research codebase. Adding a
file-based loader (YAML/TOML into these same dataclasses) is
straightforward future work if/when experiments need to be defined
outside of Python — e.g. for a batch runner sweeping many condition files.

## Reproducibility

Every stochastic step in a run — genome initialization, environment reset,
organism action sampling, mutation, selection with randomness — draws from
exactly one `numpy.random.Generator`, created once in
`EvolutionEngine.__init__` from `EvolutionConfig.seed`, and threaded
through every stage of `EvolutionEngine.step()` in a fixed order (see
`docs/architecture.md`). Two `EvolutionEngine`s built from identical
configs and the same seed therefore draw the identical sequence of random
numbers and produce byte-identical trajectories — verified directly by
running `experiments/baseline.py --seed 0` twice and diffing the output
JSON (identical) versus running it with a different seed (thousands of
differing lines). `tests/test_evolution_engine.py::test_run_is_fully_deterministic_given_same_seed`
and `tests/test_experiments.py::test_same_config_and_seed_reproduce_identical_results`
check this at the unit level.

## `ExperimentResult`: a self-contained record

`ExperimentRunner.run()` returns an `ExperimentResult` containing:

- `name`, `seed` — identifies what produced this result.
- `software` (`SoftwareMetadata`) — GENEVRA version, Python version, NumPy
  version, so a result can later be checked against the environment that
  produced it.
- `trajectory` — the full per-generation metric history
  (`genevra.metrics.trajectory.Trajectory.to_dict()`), plain
  dicts/lists/primitives.
- `lineage` — every individual's compact ancestry record
  (`genevra.evolution.lineage.LineageTracker.to_dicts()`).
- `final_population_size`, `generations_completed`, `status`
  (`"completed"` or `"extinct"` — see below).

`ExperimentResult.to_dict()` is `json.dumps`-able directly. This is
deliberately *not* a pickle of arbitrary simulation state: no raw
per-step trajectories, no live `Organism`/`GridWorld` objects, no NumPy
arrays that would need a custom encoder. What's stored is exactly what a
later analysis or comparison needs — the explicit schemas defined in
`genevra.metrics.trajectory` and `genevra.evolution.lineage`.

## Status and extinction

A run's `status` is `"completed"` if it ran all configured generations, or
`"extinct"` if, in some generation, no individual's final energy met the
reproduction eligibility threshold — the population is then set to empty
and the run stops immediately rather than continuing silently with zero
individuals. The generation at which this happened is still recorded in
the trajectory (`GenerationSnapshot.extinction = True`), and
`generations_completed`/`final_population_size` reflect the early stop.
This is a deliberate choice not to hide a failed run: an extinct
population is a real experimental outcome (e.g. reproduction eligibility
set too strict for the environment's resource density), not an error to
be swallowed.

## The baseline experiment

`experiments/baseline.py` is a small, fast (a few seconds), reproducible
demonstration that exercises the full pipeline: a population of 24
organisms, 15 generations, tournament selection with a small elite
fraction, Gaussian mutation with heritable rate/sigma, an energy-threshold
reproduction eligibility rule, and per-generation metric collection
(fitness summary, genotypic/behavioral diversity, novelty, survival rate,
mean mutation rate/sigma). Run it with:

```bash
python experiments/baseline.py --seed 0
python experiments/baseline.py --seed 0 --output results/baseline_seed0.json
python experiments/baseline.py --seed 0 --evolvability-samples 12
```

`--evolvability-samples` is opt-in (default `0`, off) and runs
`genevra.metrics.evolvability.EvolvabilityAnalyzer` on one genome from the
final population after the run completes — it is not part of the default
per-generation cost.

This is a demonstration substrate for the Phase 3 + 4 machinery, not a
scientific result: 15 generations of 24 organisms on one environment
configuration and one random seed is nowhere near enough to support any
claim about open-ended evolution, emergent intelligence, or evolvability
having evolved. Its job is to prove the pipeline works end to end and is
reproducible, which the validation in this repository's commit history
does by actually running it, not by asserting it would work.

## Controlled comparisons

`genevra.analysis.comparison.ComparisonRunner` (see `docs/analysis.md`)
runs the same seed list across two or more named conditions and returns a
`ComparisonResult` with every run's result keyed by condition, plus
explicit failure reporting. Build two `ExperimentConfig`-producing
functions that differ in exactly the variable under test (e.g. two
`GridWorldConfig`s with different `dynamics`, or two `MutationOperator`s)
and pass them as `conditions={name: factory}` — the runner guarantees the
same seed sequence is used for every condition, so "condition A, seed 3"
and "condition B, seed 3" start identically and differ only in whatever
the factories actually configure differently.

## Controlled baseline experiments (Phase 5 + 6)

Three small, fast, reproducible comparison scripts under `experiments/`
validate this infrastructure end to end, each with an explicit hypothesis,
independent variable, dependent measurements, controlled variables, and
seed policy documented in its own module docstring:

- **`exp1_isolated_vs_shared.py`** — isolated single-organism episodes
  (`EvolutionEngine` + `GridWorld`) vs. a shared multi-agent world
  (`ContinuousEvolutionEngine` + `SharedGridWorld`), compared on final
  genotypic diversity (the one metric directly comparable across both
  engines' data models — see `docs/ecology.md` for why behavioral
  diversity is not compared here).
- **`exp2_static_vs_changing.py`** — `StaticDynamics` vs.
  `RegimeChangeDynamics` (same average regeneration rate), compared on
  `instantaneous_novelty`, `genotypic_diversity`, and
  `behavioral_diversity` trajectories via `ComparisonRunner` and
  `aggregate_metric_across_runs`.
- **`exp3_fixed_vs_heritable_mutation.py`** — a condition-local
  `FixedRateMutation` (pins `mutation_genes` to a constant after every
  mutation) vs. the default heritable `GaussianMutation`, compared on
  `mean_mutation_rate`/`mean_mutation_sigma`/`genotypic_diversity`.

Run any of them with `--seeds 0 1 2 3 4` (the default) and optionally
`--output path.json`. Each is an **infrastructure-validation experiment**:
it demonstrates the comparison machinery works and is reproducible at a
small scale (a few seeds, a handful of generations/steps, runs in single-
digit seconds) — not a scientific finding. See
`docs/research_questions.md` for the distinction between what these
demonstrate and what would actually count as evidence for GENEVRA's
underlying research questions.
