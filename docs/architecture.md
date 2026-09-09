# GENEVRA Architecture

This document describes the module boundaries: which are implemented, and
which are planned separations of concerns that future phases fill in, one
validated component at a time. See also [`environment.md`](environment.md),
[`organism.md`](organism.md), [`metrics.md`](metrics.md), and
[`experiments.md`](experiments.md) for the design rationale behind each
implemented layer.

## Layers

- **`genevra.simulation`** — environment dynamics: state representation,
  stepping, sensor/action interfaces for organisms. No evolution or
  learning logic lives here. (Implemented: `GridWorld`, the `Environment`
  protocol, `VectorEnvironment`. See `environment.md`.)
- **`genevra.organism`** — the digital organism: genome, phenotype,
  controller, sensors, memory, within-lifetime learning, metabolism,
  mutation, and a single-organism reproduction interface. (Implemented.
  See `organism.md`.)
- **`genevra.evolution`** — population-level search: many organisms,
  discrete generations, selection, population-level reproduction,
  mutation, and ancestry tracking. (Implemented — see below and
  `genevra/evolution/__init__.py`.)
- **`genevra.metrics`** — measurement: fitness summary, genotypic and
  behavioral diversity, novelty, mutation-neighborhood evolvability
  analysis, and structured per-generation trajectories. Metrics are
  computed from evolution/simulation state, never the reverse. (Implemented
  — see `metrics.md`.)
- **`genevra.experiments`** — orchestration: a config (`ExperimentConfig`)
  wraps an `EvolutionConfig`; `ExperimentRunner.run()` executes it and
  returns a self-contained, JSON-serializable `ExperimentResult`.
  (Implemented — see `experiments.md`.)
- **`genevra.analysis`** — post-hoc analysis over persisted experiment
  outputs (comparison across runs/conditions, later: automated hypothesis
  discovery). (Planned.)
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
generation. The two are not yet unified because overlapping generations
don't exist yet — see the Phase 5/6 recommendations below.

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

## Status

**Phase 1–4 complete:** environment/world engine (`simulation`), digital
organism foundation (`organism`), population/evolution engine
(`evolution`), and metrics + experiment orchestration (`metrics`,
`experiments`) are implemented and tested — see `environment.md`,
`organism.md`, `metrics.md`, and `experiments.md`. Only `genevra.analysis`
(post-hoc cross-run comparison, automated hypothesis discovery) remains
unimplemented; see the README's Development Status section and this
document's evolution-layer notes above for what's deliberately deferred
within the implemented layers (overlapping generations, sexual
reproduction/recombination, ecological interaction, speciation,
migration).
