# Statistical Protocol for Phase 9/10 Analysis

## Exploratory vs. confirmatory

Everything the discovery engine produces from scanning stored results
(`genevra.discovery.correlation`, `genevra.discovery.phenomena`,
`genevra.discovery.anomaly`) is **exploratory** unless a comparison was
declared in advance as a primary analysis. `genevra.discovery
.multiple_testing.FDRResult.label` is `"exploratory"` by default and only
`"confirmatory"` when the caller explicitly passes `is_primary=True` for
that specific comparison. A low q-value on an exploratory finding is a
reason to propose a follow-up experiment (Phase 10.6), not a reason to
report it as established.

## Unit of analysis

`genevra.discovery.correlation` operates on **one row per (experiment,
seed) run** (`RunSummary`), never on raw per-generation values pooled
across a run. Treating thousands of generations from one run as
thousands of independent samples would be pseudoreplication — generations
within a run are highly autocorrelated, not independent observations.
Nothing in the correlation/hypothesis pipeline accepts a bare trajectory
for this reason.

## Multiple comparisons

Scanning many variable pairs at once inflates the chance that some
comparison looks "significant" purely by chance. `genevra.discovery
.multiple_testing.benjamini_hochberg` applies the standard
Benjamini-Hochberg false discovery rate procedure across the whole family
of comparisons examined together, producing an adjusted `q_value` per
comparison. `genevra.discovery.hypothesis.hypotheses_from_correlations`
additionally requires an effect-size threshold (not just FDR
significance) before generating a hypothesis — effect-size filtering,
Phase 10.13's second lightweight safeguard.

## Discovery vs. validation data

A pattern found in one set of seeds is not robust until checked against
seeds that played no role in finding it. `genevra.discovery.replication
.split_seeds` deterministically partitions a seed pool into
`discovery_seeds` and `validation_seeds` with no overlap
(`SeedSplit.__post_init__` raises if they overlap).
`genevra.discovery.replication.ReplicationRunner.evaluate` independently
raises if the `original` and `replication` `EvidenceSet`s share any seed.
`genevra.discovery.followup.generate_followup_experiment` defaults
`seed_start=10_000`, well above typical discovery-seed ranges, as a
further guard against accidental reuse.

## Confidence intervals, not p-value fishing

Replication confirmation (`ReplicationResult.replicated`) is judged by a
percentile bootstrap confidence interval
(`genevra.analysis.aggregation.bootstrap_confidence_interval`) excluding
zero and agreeing in sign with the original evidence — not by searching
for the smallest available p-value. Correlation p-values themselves are
permutation-test p-values (not parametric), matching the non-parametric
approach used throughout `genevra.analysis.aggregation` for the small
seed counts GENEVRA experiments realistically use.

## What none of this proves

No component in `genevra.discovery` establishes causation. A supported
hypothesis, a significant correlation, or a successful replication is
evidence consistent with the hypothesis under the conditions tested — not
proof the mechanism is real, general, or causal. See
`docs/hypothesis_protocol.md` for the exact evaluation criteria, and each
module's own docstring for the specific limitation that module's method
carries.
