# Controlled Ecological Perturbation Experiments

Module: `genevra.population_analysis.perturbation`.

## Design: before / during / after

`run_perturbation_experiment(engine, before_steps, during_steps,
after_steps, apply_perturbation, metric)` steps an already-initialized
`ContinuousEvolutionEngine` through three windows, recording
`metric(engine)` once per step in each: a `before` baseline, a `during`
window where `apply_perturbation(engine)` was called exactly once at the
boundary, and an `after` recovery window.

`apply_perturbation` is caller-supplied — e.g.
`engine.environment.perturb_resources("A", remove_fraction, rng)` (added
to `SharedGridWorld` alongside the Phase 15/16 work: zeroes a random
fraction of currently-present cells of one resource type; cleared cells
can respawn normally afterward). Other perturbations described in the
Phase 16 spec (introduce a competing population, alter patch
connectivity, change interaction strength) are not yet wired into a
single helper function — they are composable from existing pieces
(`Metapopulation.spawn_migrant`, changing a `MigrationConfig` mid-run)
but no ready-made "introduce competitor" function exists yet.

## Resistance and recovery are reported separately

`evaluate_perturbation_windows`:

- `resistance = mean(before) - min(during)`: how far the metric dropped
  during the perturbation, for a metric where lower is worse (population
  size, diversity). A metric can resist (small drop) without recovering,
  or recover slowly after not resisting at all — collapsing these into
  one number would hide which happened, so they are always two separate
  fields.
- `recovered`: whether the `after` window's values ever met
  `mean(before) * (1 - recovery_tolerance)` (default tolerance 10%).
- `recovery_step_index`: the first `after`-window index that met that
  threshold, or `None` if it never did.

Both are `None` if the `before` or `during` window has no data.

## What this does and does not establish

A single perturbation run on a single seed shows *what happened this
time* — it does not establish that the perturbation caused the observed
resistance/recovery pattern, nor that the pattern would replicate under a
different seed. Treat `docs/ecological_statistics.md`'s replication-unit
rule as applying here too: a real claim about perturbation resilience
needs the same experiment repeated across several independent seeds, with
per-seed resistance/recovery values aggregated via
`genevra.population_analysis.replication_consistency`, not one run's
numbers reported as if they generalized.

## `genevra perturbation` CLI

Runs one small resource-removal perturbation (default: 80% of resource A
removed for a short "during" window) against a fresh
`ContinuousEvolutionEngine`, prints resistance/recovery — a laptop-scale
demonstration of the mechanism, not a validated resilience finding.
