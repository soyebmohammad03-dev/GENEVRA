# GENEVRA Architecture

This document describes the module boundaries: which are implemented, and
which are planned separations of concerns that future phases fill in, one
validated component at a time. See also [`environment.md`](environment.md),
[`organism.md`](organism.md), [`metrics.md`](metrics.md),
[`experiments.md`](experiments.md), [`ecology.md`](ecology.md),
[`analysis.md`](analysis.md), and
[`research_questions.md`](research_questions.md) for the design rationale
behind each implemented layer and what it does/doesn't establish.

## Layers

- **`genevra.simulation`** — environment dynamics: state representation,
  stepping, sensor/action interfaces for organisms. No evolution or
  learning logic lives here. (Implemented: `GridWorld` and the new
  multi-agent `SharedGridWorld`, the `Environment` protocol,
  `VectorEnvironment`, `EnvironmentDynamics`, `InteractionSystem`. See
  `environment.md` and `ecology.md`.)
- **`genevra.organism`** — the digital organism: genome, phenotype,
  controller, sensors, memory, within-lifetime learning, metabolism,
  mutation, and a single-organism reproduction interface. (Implemented.
  See `organism.md`.)
- **`genevra.evolution`** — population-level search: many organisms,
  both non-overlapping discrete generations (`EvolutionEngine`) and a new
  overlapping-generations mode (`ContinuousEvolutionEngine`), selection,
  population-level reproduction, mutation, and ancestry tracking.
  (Implemented — see below, `ecology.md`, and `genevra/evolution/__init__.py`.)
- **`genevra.metrics`** — measurement: fitness summary, genotypic and
  behavioral diversity, novelty (cumulative and instantaneous),
  mutation-neighborhood evolvability analysis, and structured
  per-generation trajectories. Metrics are computed from evolution/
  simulation state, never the reverse. (Implemented — see `metrics.md`.)
- **`genevra.experiments`** — orchestration: a config (`ExperimentConfig`)
  wraps an `EvolutionConfig`; `ExperimentRunner.run()` executes it and
  returns a self-contained, JSON-serializable `ExperimentResult` —
  including explicit `failure` information for runs that raised, rather
  than crashing. (Implemented — see `experiments.md`.)
- **`genevra.analysis`** — post-hoc analysis over persisted experiment
  results: multi-run/multi-seed aggregation, controlled comparisons
  (`ComparisonRunner`), evolutionary stagnation detection, lineage
  analysis, and evolvability-over-time sampling. Never reaches into a
  live simulator. (Implemented — see `analysis.md`. Automated hypothesis
  discovery remains planned.)
- **`genevra.visualization`** — lightweight, reproducible plots
  (fitness/novelty/diversity trajectories, population size, lineage
  survival, evolvability over time) built from stored results, never from
  a live simulation. `matplotlib` is an optional dependency
  (`pip install -e ".[viz]"`), imported lazily so the core package stays
  numpy-only. (Implemented.)
- **`genevra.cli`** — the `genevra` command (`run`, `analyze`, `inspect`,
  `compare`) — plain `argparse`, no new CLI framework dependency.
  (Implemented.)
- **`genevra.utils`** — cross-cutting concerns with no research content:
  reproducible seeding, logging. (Implemented.)
- **`genevra.arrays`** — shared NumPy array type aliases (`FloatArray`,
  `BoolArray`) used across `simulation`, `organism`, `evolution`, and
  `metrics`. (Implemented.)

## The population/evolution layer

`genevra.evolution` uses non-overlapping discrete generations: `Population`
holds the current generation's `Individual`s (id, genome, generation,
parent ids); `EvolutionEngine.step()` runs one generation as an explicit
sequence of stages rather than one undifferentiated function — run every
individual's lifetime (`evolution.lifetime.run_single_lifetime`, the same
function `genevra.metrics.evolvability` reuses for its own single-genotype
evaluations), compute fitness, determine which individuals are
reproduction-eligible (`evolution.reproduction.PopulationReproduction`,
an energy-threshold rule over each lifetime's final energy), select
parents from the eligible pool (`evolution.selection.SelectionStrategy` —
fitness-proportional, tournament, or elitist-wrapping-another-strategy,
chosen per experiment, never hardcoded), produce one mutated offspring
genome per selection draw, record the resulting `GenerationSnapshot`
(`genevra.metrics.trajectory`), and record births/deaths/reproduction
events in `evolution.lineage.LineageTracker`.

`evolution.reproduction.PopulationReproduction` is deliberately a separate
implementation from `organism.reproduction.ReproductionSystem` (Phase 2):
the latter models a single *still-living* organism deciding, during its
own lifetime, whether it has enough energy to reproduce — a hook intended
for a future overlapping-generations or continuous-time model where
organisms coexist and reproduce asynchronously. `PopulationReproduction`
is the discrete-generation batch analog: by the time it runs, every
individual's lifetime has already ended, so there's no "still alive"
organism to ask; it only decides eligibility from the recorded final
energy and generates offspring genomes for the next, entirely-replacing
generation. `genevra.evolution.continuous.ContinuousEvolutionEngine` (new
this phase) is the overlapping-generations counterpart these two were
foreshadowing — see `ecology.md`. The two engines remain separate rather
than unified into one, since their control flow (whole-generation batches
vs. per-tick individual birth/death) is genuinely different, not just a
configuration knob.

If no individual in a generation meets the reproduction eligibility
threshold, `EvolutionEngine` records the generation as `extinction=True`
in its trajectory, empties the population, sets `RunStatus.EXTINCT`, and
stops — this is a real, recorded outcome, not a silently swallowed error
(see `experiments.md`).

Lineage (`evolution.lineage.LineageTracker`) stores one compact
`LineageEvent` per individual (id, parent id(s), birth generation, a short
genome hash, death generation, whether it reproduced) — not a copy of
every historical genome — sufficient to reconstruct ancestry chains
(`ancestors()`, `children()`) and, later, family trees and lineage
survival/branching analysis without carrying a full object graph.

## Why this separation

Evolvability is a first-class research question here, not a side effect —
so `learning` (within-lifetime, `genevra.organism.learning`) and
`evolution` (across-generation) are distinct modules with an explicit
interface between them (a genome's `learning_genes`), rather than one
hardcoded update loop. `metrics` is likewise independent of
`simulation`/`evolution` so that novelty, diversity, and evolvability
measures can be swapped or compared without touching the systems they
measure — `EvolutionEngine` depends on `genevra.metrics`, but no
`genevra.metrics` module depends on `EvolutionEngine`, only on the lower-
level `evolution.lifetime` data types, keeping metrics reusable outside
the main generational loop (as `EvolvabilityAnalyzer` is).

## Known performance limitation

Profiling `experiments/baseline.py` (24 organisms × 15 generations × 80
steps) shows `GridWorld._extract_local_grid`'s `np.pad` call accounting
for roughly 28% of total runtime — it re-pads the entire obstacle/resource
grid on every single step just to read out a small window. This is a
genuine, identified bottleneck (found by profiling, not assumed), not yet
fixed: at baseline scale the whole run still completes in ~3 seconds, so
there was nothing forcing the optimization yet. A grid large enough, or a
population/generation count high enough, to make this matter would be the
trigger to replace it with a bounds-checked direct slice (no padding
allocation) instead.

**This bottleneck is worse, and now the clear top priority, in the shared/
multi-agent path.** Profiling `ContinuousEvolutionEngine` (12-20 agents,
14x14 `SharedGridWorld`, 600 ticks) shows `SharedGridWorld._extract_local_grid`
accounting for roughly **64%** of total runtime — every agent's `observe()`
call re-pads the *entire* grid independently every tick, so the cost now
scales with `agent_count x steps` rather than just `steps`. The fix is the
same one identified for `GridWorld` (a bounds-checked direct slice instead
of `np.pad`), and would help proportionally more here. Not fixed in this
phase — correctness and coverage came first, per "profile before
optimizing" — but this is now the single most impactful place to optimize
before scaling shared-world population sizes much further.

## Status

**Phase 1–6 complete:** environment/world engine, digital organism
foundation, population/evolution engine (discrete and overlapping-
generations), ecological/multi-agent simulation, metrics, analysis
(aggregation, controlled comparison, stagnation detection, lineage
analysis, evolvability-over-time), experiment orchestration, a CLI, and
lightweight visualization are all implemented and tested. Deliberately
not built: sexual reproduction/recombination, speciation, migration
between environments, hazard cells/predation/communication/cooperation
(the `InteractionSystem`/`EnvironmentDynamics` protocols support adding
these later without redesign), automated hypothesis discovery, and a
family-tree visualization (lineage *analysis* exists; a genealogy
*visualization* does not). See `docs/research_questions.md` for what the
implemented measurement machinery does and does not establish about
GENEVRA's actual research questions.
