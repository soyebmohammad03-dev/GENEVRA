# Analysis and Controlled Comparison

Module: `genevra.analysis` (`aggregation.py`, `comparison.py`,
`stagnation.py`, `lineage_analysis.py`, `evolvability_over_time.py`).

Everything in this package consumes recorded results — `ExperimentResult`
dicts, `Trajectory`/`GenerationSnapshot` data, `LineageTracker` — never a
live simulator. Nothing here reaches back into hidden state; a result
computed once can always be re-analyzed later from its stored JSON.

## Multi-run aggregation

A single evolutionary run is not a scientific result. `genevra.analysis.aggregation`
provides:

- `aggregate_metric_across_runs(trajectories, extract)` — one
  `MetricAggregate` (mean, median, std, and a percentile spread) per
  generation, computed over whichever runs still have data at that
  generation. Runs that ended early (extinction) are neither padded to a
  common length nor silently dropped: `MetricAggregate.n_runs` shrinks
  honestly across the x-axis as shorter runs run out of data.
- `final_generation_values(trajectories, extract)` — each run's *actual*
  last generation's value (not a fixed generation index), for comparing
  final outcomes across runs of possibly different lengths.
- `area_under_trajectory(values)` — trapezoidal-rule area under a
  per-generation series, a single-number summary (e.g. "total novelty
  accumulated") without needing a plot.
- `permutation_test(sample_a, sample_b, rng)` — the one **inferential**
  method in this module (everything else is descriptive): a real,
  computed non-parametric permutation test for a difference in means,
  appropriate for the small, non-normal sample sizes (a handful of seeds)
  GENEVRA experiments realistically use — chosen instead of a t-test
  specifically because a t-test's normality assumption would not be
  justified there. No parametric confidence interval is computed anywhere
  in this module, and no p-value is ever fabricated: `permutation_test`'s
  p-value is a real fraction of permutations at least as extreme as the
  observed difference (with `+1/+1` smoothing so it is never exactly
  zero).

## Controlled comparison: `ComparisonRunner`

`genevra.analysis.comparison.ComparisonRunner` takes a `{condition_name:
config_factory}` mapping and a `seeds` list, and calls
`config_factory(seed)` for every `(condition, seed)` pair — the same seed
list under every condition. This is what makes a comparison *controlled*
rather than confounded: "condition A, seed 3" and "condition B, seed 3"
start from the same seed and differ only in whatever the two factory
functions actually configure differently (see
`experiments/exp2_static_vs_changing.py` and
`experiments/exp3_fixed_vs_heritable_mutation.py`, where the factories
are identical except for exactly one field). `ComparisonRunner` does not
and cannot verify that a caller's two factories only differ in the
intended variable — that discipline is the experiment author's
responsibility, stated explicitly here rather than silently assumed.

Failures are represented, not silently dropped: `ExperimentRunner.run()`
catches any exception raised during a run and returns a `status="failed"`
result with a populated `failure` field (exception type + message) instead
of propagating — one bad seed/condition cannot crash an entire
comparison. `ComparisonResult.failures()` surfaces every failed run
explicitly.

## Evolutionary stagnation analysis

`genevra.analysis.stagnation.StagnationAnalyzer` computes, over a trailing
window of generations, whether behavioral novelty, genotypic diversity,
behavioral diversity, and (if separately supplied) evolvability are on a
declining trend (least-squares slope below an explicit, configurable
threshold — every threshold is a field on `StagnationConfig`, never a
constant hidden in a function body). `stagnation_score` is the simple,
transparent fraction of evaluated signals that triggered — not a
validated statistical model of "how stagnant."

**Fitness plateau is computed and reported (`fitness_plateaued`), and is
structurally excluded from `stagnation_score` and `contributing_signals`
— no code path in this module ever adds it to the combined signal.** A
population can stop increasing in fitness while continuing to produce
genuinely novel behavior, or its fitness can plateau purely because the
fitness function saturated, with no bearing on whether the population is
still evolving interesting variation. Conflating the two would misuse the
tool for the exact failure mode GENEVRA's scientific-integrity
requirements exist to prevent. This is tested directly:
`tests/test_stagnation.py::test_fitness_plateau_alone_never_triggers_stagnation_signals`
constructs a trajectory with a flat fitness mean and *rising* novelty/
diversity, and asserts `stagnation_score == 0.0` and that no
fitness-related string ever appears in `contributing_signals`.

## Novelty trajectories: cumulative vs. instantaneous

`GenerationSnapshot` carries both `mean_novelty` (**cumulative/
historical**: each individual's behavioral signature scored against the
persistent, size-capped `NoveltyArchive` built up over the whole run so
far) and `instantaneous_novelty` (scored only against *this generation's*
own signatures, leave-one-out, ignoring all history). These answer
different questions — "how different from everything seen so far" vs.
"how different from current peers" — and are never collapsed into one
number. The archive itself has a configurable capacity
(`EvolutionConfig.novelty_archive_size`) and a documented eviction policy
(random eviction once full — see `docs/metrics.md`), so it cannot grow
unboundedly.

## Diversity trajectories: genotype vs. phenotype vs. behavior

Genotypic and behavioral diversity are tracked separately in every
`GenerationSnapshot` (see `docs/metrics.md`). **Phenotype diversity is
deliberately not implemented as a third, separate metric in this
version**: GENEVRA's current genotype-to-phenotype map (`develop()`) is a
deterministic bijection — a pure reshape of `controller_weights` into
weight matrices, with no developmental noise, gene regulation, or
redundant encoding. A phenotype-diversity metric computed today would be
numerically identical to genotypic diversity, so reporting both would
misrepresent one number as two independent measurements. This will become
a meaningful, distinct metric once the genotype-to-phenotype map itself
becomes non-trivial — noted here as a concrete future direction, not
silently glossed over.

Combinations such as "high fitness + low behavioral diversity" or
"low fitness + high novelty" are representable directly from a stored
trajectory (read the relevant fields side by side) but this package does
not interpret them automatically — GENEVRA reports the numbers; deciding
what a particular combination means for a particular run is left to the
person running the experiment.

## Evolvability over time

`genevra.analysis.evolvability_over_time.sample_evolvability_over_generations`
drives an `EvolutionEngine` generation by generation, and at a
caller-chosen set of generations, samples a bounded number of genomes
(via a `SamplingStrategy` — `RandomSampling`, `TopScoreSampling` for any
`Genome -> float` score, or `LineageSampling` for one representative per
distinct founding lineage) and runs `EvolvabilityAnalyzer` on each. Both
the number of sampled generations and the number of genomes per
generation are explicit, caller-controlled parameters — this is never run
automatically as part of a normal `EvolutionEngine` run, so mutation-
neighborhood sampling cost is always a deliberate choice, not an
automatic per-generation tax. See `docs/metrics.md` for what an
`EvolvabilityReport` does and does not claim.

## Lineage analysis

`genevra.analysis.lineage_analysis.summarize_lineages` groups every
recorded individual by its founding ancestor and reports per-lineage
size, generational reach, and whether/when it went extinct.
`dominant_lineage` (purely descriptive — "which founder's descendants
make up the most of the run," not a claim about evolutionary success) and
`lineage_diversity` (normalized Shannon entropy over lineage sizes, `0`
for total dominance by one lineage, `1` for perfectly even lineages) are
built on top. This is the data foundation for later family-tree
visualization and lineage-branching analysis — not the visualization
itself, which does not exist yet.

## Result schema

`ExperimentResult` (`genevra.experiments.result`) now also carries
`environment_summary` (the environment config as a plain dict — includes
`dynamics`, since `GridWorldConfig`/`EnvironmentDynamics` implementations
are dataclasses and serialize recursively), `condition_id` (set by
`ComparisonRunner`/`ExperimentRunner` when running as part of a named
comparison), and `failure` (populated only for `status="failed"` runs).
Everything remains plain dicts/lists/primitives — `to_dict()` is directly
`json.dumps`-able, with no custom encoder needed.
