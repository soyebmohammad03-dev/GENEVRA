# GENEVRA Research Protocol v1

This is GENEVRA's first formal research protocol: the specific,
operational plan for testing whether evolvable learning strategies
change evolutionary dynamics, distinct from `docs/research_questions.md`
(which frames the broader open questions and what would count as
evidence for each, conceptually). This document specifies *this* study:
exact conditions, controls, seed policy, and confounds, so a run can be
reproduced and judged against a pre-committed plan rather than a
post-hoc story.

## Research question

Can evolutionary systems evolve learning strategies that improve
adaptation and evolutionary novelty — as opposed to lifetime learning
being either irrelevant or purely a fixed, non-evolvable mechanism?

## Hypothesis

Populations that can evolve their learning strategy (heritable,
mutable `learning_genes` — see `genevra.organism.learning.LearningParams`)
will show measurably different evolutionary dynamics — in fitness,
learning gain, behavioral novelty, or evolvability — from populations
with no lifetime learning, or with a fixed (non-evolving) learning
strategy, under matched conditions.

This is stated as a testable hypothesis, not an assumption. GENEVRA's
machinery must be able to report evidence *against* it (no detectable
difference, or a difference in the opposite direction) as legitimately
as evidence for it.

## Primary comparison: three conditions

Built by `genevra.experiments.conditions.apply_learning_condition` from
one shared base `EvolutionConfig`, so the three conditions differ only
in `learning_rule_factory` and whether `learning_genes` mutate:

| Condition | `LearningCondition` | Learning rule | `learning_genes` heritable? |
|---|---|---|---|
| A. No learning | `NO_LEARNING` | `NoLearning` | irrelevant (rule ignores them) |
| B. Fixed learning | `FIXED_LEARNING` | `HebbianLearning` | No — fixed at founder value all run |
| C. Evolvable learning | `EVOLVABLE_LEARNING` | `HebbianLearning` | Yes — mutated like any gene group |

## Secondary factors

Each of the three conditions above is additionally run under:

1. **Stable environment** — `GridWorldConfig.dynamics=None` (fixed
   `resource_regen_prob`).
2. **Changing environment** — `PeriodicDynamics` or
   `RegimeChangeDynamics` (see `genevra.simulation.dynamics`), so the
   environment itself is non-stationary within a lifetime/run.
3. **Environment-shift generalization** — evolution proceeds entirely
   under condition 1's environment; `EvolutionConfig.eval_environment_config`
   is set to a *held-out* environment (e.g. different `resource_density`)
   that the population is evaluated on every generation but never
   selected on (`EvolutionEngine._evaluate_generalization` — the eval
   run's fitness never enters `eligible_indices`/selection). Training
   fitness (`GenerationSnapshot.fitness_summary`) and evaluation fitness
   (`GenerationSnapshot.eval_fitness_summary`) are reported as separate
   fields, never combined.

Ecological interaction (shared vs. isolated episodes, `SharedGridWorld`
vs. `GridWorld`) is a documented axis in `docs/ecology.md` and Experiment
1, but is **not** crossed with the three learning conditions in this
first protocol — that is a Phase 9+ extension, to keep the first
protocol's condition count laptop-feasible (3 learning conditions x 3
environment regimes x N seeds already scales as `9N` full evolutionary
runs).

## Primary measurements

Per generation (from `GenerationSnapshot`, and `genevra.metrics.adaptation`
computed over sampled individual lifetimes):

- `fitness_summary` (training) and `eval_fitness_summary` (generalization)
- `learning_gain` (`AdaptationCurve.learning_gain` — final minus initial
  competence within a lifetime, from `rewards_by_step`)
- `instantaneous_novelty` / cumulative `mean_novelty`
- `behavioral_diversity`, `genotypic_diversity`
- `learning_gene_stats` (Phase 8.8 distribution summary — mean is not
  enough; a population that splits into two co-existing strategies is
  visible only in quantiles)
- Evolvability (`EvolvabilityAnalyzer`, sampled at generation checkpoints
  via `sample_evolvability_over_generations` — an on-demand cost, not a
  per-generation default)
- Stagnation indicators (`StagnationAnalyzer`, trend-based over novelty/
  diversity/evolvability, never fitness-plateau alone — see
  `genevra.analysis.stagnation`)

## Controls

- **Seed policy**: `genevra.analysis.comparison.ComparisonRunner` runs
  the same seed list across every condition (`condition_factory(seed)`
  for the same `seeds` for every condition name) — "condition A, seed 3"
  and "condition C, seed 3" start from the same environment/organism/RNG
  seed. Use as many seeds as the computational budget allows; a pilot
  (below) uses a small number to validate the pipeline, a real study
  should use substantially more (at minimum enough that
  `bootstrap_confidence_interval`/`cohens_d` in
  `genevra.analysis.aggregation` produce intervals narrow enough to be
  informative — check `n_observations` before trusting a reported CI).
- **Population size, generation count, mutation budget, environment
  budget, model architecture**: held fixed across all three conditions
  via the shared base `EvolutionConfig` that `apply_learning_condition`
  copies from — verified automatically by
  `genevra.analysis.comparison.validate_comparison`, which raises on
  conditions with different run counts or missing seeds and warns on
  mismatched environment configurations, software versions, or
  inconsistent completed-generation counts.
- **Ablation framework** (`genevra.experiments.conditions.AblationConfig`/
  `apply_ablations`) exists for isolating one mechanism at a time
  (learning, heritable learning params, heritable mutation strength,
  changing environment) beyond the three named conditions, for follow-up
  studies that want a finer-grained factor breakdown.

## Potential confounds

- **Environment difficulty** differing between the "stable" and
  "changing" secondary conditions in ways unrelated to dynamics per se
  (e.g. mean resource availability, not just its variance) — check
  `environment_summary` fields for this before attributing a difference
  to "changing vs. stable" rather than "harder vs. easier."
- **Selection pressure / mutation rate / population size** differing
  between runs by accident rather than by design — guarded by
  `validate_comparison`, but only for the fields it checks; a new
  confound axis added later needs a corresponding check.
- **Computational budget** differing between conditions (e.g. one
  condition hitting `max_runtime_seconds` before another) — `RunStatus.BUDGET_EXCEEDED`
  is a distinct, visible status (never silently reported as `COMPLETED`)
  specifically so this confound is detectable rather than hidden.
- **Metric archive size** (`NoveltyArchive.max_size`) — held fixed across
  conditions in the base config; a larger archive for one condition would
  make its `mean_novelty` not directly comparable to another's.

## What would count as evidence

A statistically and practically meaningful difference (effect size via
`cohens_d`, not p-value alone) between conditions B and C (isolating the
effect of *evolvability of learning strategy* specifically, holding "does
learning happen at all" fixed) in fitness, learning gain, novelty, or
evolvability, that:

- holds across the seed set (not driven by one outlier seed),
- is not attributable to a confound `validate_comparison` or a manual
  review of `environment_summary` would catch, and
- is consistent in direction between the stable and changing-environment
  secondary conditions, or is explicitly reported as regime-dependent if
  it is not.

## What would NOT count as evidence

- One seed showing condition C's final fitness numerically higher than
  B's.
- A difference in `mean_novelty` alone without checking whether it is
  driven by `NoveltyArchive` size or eviction-policy randomness rather
  than genuine behavioral change.
- A rising per-lifetime reward trend (`learning_gain > 0`) in condition C
  without a `NoLearning` control (condition A) run under matched
  conditions — `genevra.metrics.adaptation` is explicit that a positive
  `learning_gain` is consistent with, but not proof of, learning being
  the cause (see that module's docstring).
- Any single combined "intelligence score" — GENEVRA deliberately keeps
  fitness, learning gain, novelty, diversity, and evolvability as
  separate fields (`genevra.analysis.tradeoff`) precisely so this kind of
  overclaiming isn't easy to produce by accident.

## Reporting

`genevra.analysis.report.build_research_report` assembles a
`ResearchReport` from a `ComparisonResult`: conditions, seeds, per-
condition metric summaries (with bootstrap CIs when an `rng` is
supplied), pairwise effect sizes between every condition pair, the
`ComparisonValidation` (errors/warnings), and explicit `limitations`.
`interpretation` is always the placeholder text explaining that
interpretation is the researcher's job — this module does not generate
claims of discovery.
