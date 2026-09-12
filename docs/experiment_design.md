# Experiment Design

How GENEVRA's experiments are structured, and the confound this
document exists to make sure doesn't recur. `docs/research_protocol.md`
is a worked example of most of what's described here, applied to one
specific study (learning-strategy conditions); this document is the
general reference.

## Config-driven experiments

Every experiment is built from an explicit, serializable configuration
— `EvolutionConfig`/`ContinuousEvolutionConfig`
(`genevra.evolution.engine`/`continuous`), `GridWorldConfig`/
`SharedGridWorldConfig` (`genevra.simulation`), `CampaignConfig`
(`genevra.campaign.config`) — never hidden global state. Two conditions
being compared should differ in exactly the fields the experiment's own
docstring says they differ in; `experiments/exp_ecology_corrected.py`'s
`_run(seed, resource_a_density)` is a template for this: one function,
called twice with only the one intended parameter changed, so it is
mechanically impossible for the two conditions to also differ in
architecture, mutation, or reproduction settings by accident.

## Seed design

Seeds are explicit and hierarchical where a design calls for it:

- A single experiment/condition takes one integer seed per replicate
  (e.g. `experiments/exp_ecology_corrected.minimal_competition(seed)`).
- A campaign derives seeds hierarchically — campaign seed -> condition
  seed -> replicate seed — via `numpy.random.SeedSequence.spawn`
  (`genevra.campaign.seeding`), so that adding a condition never changes
  another condition's seed stream, and changing the campaign seed
  changes every condition's seeds together, deterministically.
- The evidence package additionally partitions its seeds into
  non-overlapping development/validation sets
  (`genevra.evidence.validation_split.split_seeds`,
  `research_evidence/seeds/development_validation_split.json`).

## Controls

A control condition should differ from the treatment condition in
exactly the independent variable under test — everything else (engine,
architecture, population mechanics, generation/update structure,
metrics) held identical. This sounds obvious and was violated by this
project's own original RQ4 experiment; see "A worked confound example"
below.

## Confirmatory vs. exploratory

See `docs/statistical_methods.md` for the statistical mechanics
(Benjamini-Hochberg families, `is_primary` labeling). At the design
level: a comparison is only confirmatory if its primary outcome,
direction, and statistical test were declared *before* execution
(`genevra.campaign.config.AnalysisPlan`, saved to disk before the
experiment runs — see below). A comparison whose metric or test was
picked after looking at results is exploratory, however interesting its
result, and must be reported as such.

## Pre-analysis plans

`genevra.campaign.config.AnalysisPlan` is a frozen dataclass — primary
outcome, secondary outcomes, expected direction, comparison,
statistical test, replication unit (hard-validated to `"seed"`),
exclusion criteria, minimum sample size — written to disk via
`AnalysisPlan.save()` before the corresponding experiment executes, and
only ever *consumed*, never regenerated, by the resulting report. The
evidence package's RQ4b correction follows this exactly:
`research_evidence/configurations/rq4_corrected_analysis_plan.json` was
written by `genevra.evidence.build._build_rq4b` before
`experiments/exp_ecology_corrected.py`'s `minimal_competition`/
`shared_competition` functions were called — a real ordering enforced by
the code's own control flow, not a claim made after the fact.

## Temporal and seed holdout

See `docs/statistical_methods.md`'s "Held-out validation" section
(`genevra.population_analysis.temporal_validation.leave_one_seed_out`/
`within_seed_holdout`). At the design level: a predictive claim
(metric at generation *t* predicting an outcome at *t+k*) is only as
strong as the holdout it survived — in-sample correlation across a
single trajectory is the weakest form of evidence a design can offer for
such a claim, genuine leave-one-seed-out is the strongest GENEVRA
currently implements.

## Provenance

Every artifact traces to the experiment, condition, seed set,
configuration hash, metric IDs, analysis version, and git commit that
produced it — see `docs/reproducibility.md`'s "Provenance" section and
`genevra.evidence.manifest.EvidenceArtifact`.

## Common confounds to check for

Before trusting a two-condition comparison, check whether the
conditions differ in more than the stated independent variable:

- **Engine/architecture**: different simulation engine classes, discrete
  vs. continuous generation structure, different selection mechanisms.
- **Sensory input shape**: a different `channels`/`input_size` on the
  organism's controller changes what the controller can even represent,
  independent of anything about ecology or learning.
- **Population mechanics**: different `max_population`/reproduction
  rules changing turnover rates for reasons unrelated to the stated
  variable.
- **Metric definition drift**: comparing a metric computed one way in
  one condition's code path against a differently-computed proxy in the
  other.

## A worked confound example: RQ4 -> RQ4b

The original RQ4 (`experiments/exp1_isolated_vs_shared.py`) set out to
test "does ecological interaction structure affect evolutionary
dynamics?" by comparing:

| | Isolated | Shared |
|---|---|---|
| Engine | `EvolutionEngine` | `ContinuousEvolutionEngine` |
| Environment | `GridWorld` | `SharedGridWorld` |
| Generations | Discrete, non-overlapping | Continuous, overlapping |
| Selection | Tournament selection | Birth/death reproduction |
| `channels` | 2 | 3 |

The permutation p=0.0005 / Cohen's d=2.77 result was real and
reproducible — but it could not be attributed to ecological interaction
structure, because four other things changed alongside it. An
independent audit (2026-09-13) caught this and downgraded the result's
`evidence_status` to `CONFOUNDED`
(`research_evidence/research_questions/RQ4.json`) — the original numbers
were kept, only their interpretation was withdrawn.

The correction, RQ4b (`experiments/exp_ecology_corrected.py`), holds
every one of those four things fixed and varies only
`resource_a_density` (a `genevra.ecology.competition`-documented
competition-strength parameter):

| | `minimal_competition` | `shared_competition` |
|---|---|---|
| Engine | `ContinuousEvolutionEngine` (same) | `ContinuousEvolutionEngine` (same) |
| Environment | `SharedGridWorld` (same) | `SharedGridWorld` (same) |
| `channels` | 3 (same) | 3 (same) |
| `resource_a_density` | 0.30 | 0.05 |

Result: Cohen's d = -0.10, raw p = 0.7303, status `NOT_SUPPORTED` — a
real, well-powered (n=24 per condition) null, not merely "no significant
effect found." See `research_evidence/tables/rq4_historical_vs_corrected.md`
for both results side by side, and
`docs/phase_17_18_quality_gate.md`/`docs/final_research_quality_gate.md`
for the fuller narrative.

The lesson this document exists to generalize: a large, statistically
significant effect is not evidence for the causal story a comparison was
designed to test unless the comparison actually isolated that one
variable. Checking this requires reading the experiment's own code, not
just its result.
