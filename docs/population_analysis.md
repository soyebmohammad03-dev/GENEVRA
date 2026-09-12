# Population-Level Analysis

Module: `genevra.population_analysis`.

## Why this package exists

Phase 13's `genevra.mechanisms` analyzers (`RobustnessAnalyzer`,
`GeneralizationAnalyzer`, mutational-landscape sampling) operate on one
genome at a time. Running them against thousands of organisms in one
evolutionary run and treating each organism as an independent
observation would be pseudoreplication — those organisms share a
selection history and are not independent draws. `genevra.
population_analysis` adds an aggregation layer *on top* of Phase 13's
math, reducing many organism/generation values to one number per
independent seed before any cross-condition statistic runs. See
`docs/ecological_statistics.md` for the replication-unit rule this
enforces everywhere.

## Aggregation layer (`aggregation.py`)

`seed_level_values({seed: [organism-or-generation values]}, reducer)` ->
`{seed: one value}`. `to_condition_sample` turns that into an
ascending-seed-ordered list, the shape every downstream statistical
function in this package expects.

## Population-level robustness (`robustness_population.py`)

`PopulationRobustnessAnalyzer.summarize(robustness_mean_by_seed, rng)`
computes mean/median/between-seed variance and a bootstrap CI (via the
existing `genevra.analysis.aggregation.bootstrap_confidence_interval`)
over one robustness value per seed. Callers are expected to have already
run Phase 13's `RobustnessAnalyzer` once per seed (typically against a
representative genome from that seed's population) — this module does
not re-run the perturbation sampling itself.

`robustness_metric_association(robustness_by_seed, other_metric_by_seed)`:
Pearson correlation at the seed level, `None` below 3 shared seeds or a
constant series — the per-seed extension of `genevra.mechanisms.
robustness.robustness_evolvability_association`.

## Population-level evolvability (`evolvability_population.py`)

`PopulationEvolvabilityAnalyzer.summarize(reports)` aggregates one
`EvolvabilityReport` per seed into `FieldDistribution`s (n, mean, std,
raw values) for `mean_behavioral_distance`, `viable_fraction`,
`beneficial_fraction`, `neutral_fraction`, `deleterious_fraction`.
Fields that are `None` for a given seed (e.g. no `fitness_evaluator` was
supplied) are excluded from that field's distribution, never treated as
zero.

## Experiment matrix (`matrix.py`)

`build_strategy_ecology_matrix` crosses Learning (`NO_LEARNING`,
`HEBBIAN` — see note below) x Ecology (`ISOLATED`, `SHARED_COMPETITION`)
x Environment (`STATIC`) at `PILOT`/`STANDARD`/`RESEARCH` size presets.
`EcologyAxis.SPATIAL` needs a `Metapopulation`, not a single
`ContinuousEvolutionConfig`, so it is built separately via
`build_metapopulation_condition`.

*"Evolvable" vs "fixed" learning is not two variants of the same
`LearningRule` class* in GENEVRA's current model: `NoLearning` never
reads `learning_genes`, `HebbianLearning` always uses whatever mutation
gave those genes. The matrix's `LearningAxis` levels are therefore
`NoLearning` vs `HebbianLearning`, not a fixed/evolvable distinction the
organism model implements as two variants of one rule.

`seed_schedule(mode, base_seed)` returns a deterministic seed sequence
(`base_seed + 0, base_seed + 1, ...`) sized to the mode's `n_seeds`.

## Lineage x ecology (`lineage_ecology.py`)

`convergent_evolution_check(events, threshold)` compares every pair of
individuals descended from *different* founders (by `parent_ids`
ancestry) and counts pairs whose `learning_strategy` Euclidean distance
is below `threshold` — a descriptive convergence-rate, not a claim about
*why* two independent lineages arrived at similar strategies. Quadratic
in population size; fine at GENEVRA's laptop-scale populations.

## See also

`docs/evolutionary_prediction.md` (lagged prediction, temporal
validation, replication consistency) and
`docs/perturbation_experiments.md` (controlled perturbations) cover the
remaining Phase 16 modules.
