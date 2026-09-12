# Statistical Methods

This is the project-wide statistical reference, covering everything used
in the committed `research_evidence/` package. `docs/statistical_protocol.md`
covers the same ground for the earlier Phase 9/10 discovery engine
specifically — this document is the broader index; where the two
overlap, `statistical_protocol.md` is the more detailed source and is
linked rather than restated.

## Replication unit

**The independent seed/run is the unit of replication for every
cross-condition statistical claim in GENEVRA**, never the individual
organism. A single evolutionary run produces many organisms, but they
share one environment history, one selection pressure, and downstream
RNG state — they are not independent draws; treating them as such is
pseudoreplication. This is enforced, not just documented:

- `genevra.campaign.config.AnalysisPlan` raises if `replication_unit`
  is set to anything other than `"seed"`.
- `genevra.population_analysis.aggregation` exists specifically to
  reduce organism/generation values to one number per independent seed
  *before* any permutation test, Cohen's d, or bootstrap CI runs.
- `genevra.discovery.correlation` operates on one row per
  (experiment, seed) run, never on raw per-generation values pooled
  across a run (`docs/statistical_protocol.md`).

See also `docs/ecological_statistics.md` for the same rule applied to
ecology/population-analysis specifically.

## Permutation tests

`genevra.analysis.aggregation.permutation_test(sample_a, sample_b, rng,
num_permutations=2000)` — a two-sided permutation test for a difference
in means between two independent samples: shuffle the pooled labels
`num_permutations` times and ask how often a difference at least as
extreme as the observed one occurs by chance. Used instead of a
parametric test (e.g. a t-test) because GENEVRA's typical sample sizes
(a handful to a few dozen independent seeds) are too small to justify a
normality assumption. The p-value uses +1/+1 smoothing (never exactly
zero, since the observed arrangement is itself one of the permutations).

## Effect size: Cohen's d

`genevra.analysis.aggregation.cohens_d(sample_a, sample_b)` — the
pooled-standard-deviation standardized mean difference. Reported
*alongside*, never instead of, the permutation test's p-value: a
p-value says whether a difference is unlikely to be chance given the
sample size; an effect size says how large the difference actually is.
Conflating the two is a common misreading this project deliberately
avoids by keeping them as separate fields from separate functions.

## Bootstrap confidence intervals

`genevra.analysis.aggregation.bootstrap_confidence_interval(sample, rng,
confidence_level=0.90, n_resamples=2000)` — a percentile-bootstrap CI
for the mean of one sample. Deliberately not a normal-approximation CI,
for the same small-sample reason permutation tests are preferred over
t-tests. `research_evidence/statistics/rq4_corrected.json` uses
`confidence_level=0.95`.

## Pearson correlation

Used for purely associational claims where no two-condition comparison
applies — e.g. RQ2 (robustness vs. evolvability) and
`plasticity_cost_association` (`genevra.mechanisms.plasticity_cost`).
Reported only with >= 3 non-missing paired observations
(`genevra.analysis.tradeoff`'s convention). A correlation is never
treated as evidence of causal direction.

## Benjamini-Hochberg FDR correction

`genevra.discovery.multiple_testing.benjamini_hochberg(p_values,
is_primary, alpha)` — the standard BH step-up procedure, correcting an
entire family of p-values together (never a subset chosen after seeing
which ones are already significant). `is_primary` only affects the
`"confirmatory"`/`"exploratory"` label, not the correction itself — every
p-value in the family is corrected together regardless.
`genevra.campaign.multiple_comparison.build_multiple_comparison_registry`
is a thin wrapper producing one `CorrectedComparisonRecord` per input,
used to build `research_evidence/statistics/rq_family_fdr.json`'s
2-test confirmatory family (RQ1/RQ6's literature-reproduction test and
RQ4b's corrected ecology test). Each family's exact membership and the
reason each excluded test was excluded is recorded in the family's own
`family_membership_rationale` field — FDR is never applied to
exploratory/descriptive analyses that never produced a formal p-value in
the first place (RQ2's plain correlation, RQ3's sign-agreement rate,
RQ5/RQ8's descriptive/insufficient-data results, RQ7's exploratory
sweep).

## Multiple-comparison families

A "family" is the set of confirmatory tests corrected together. Building
the wrong family — too narrow (leaving out a real confirmatory test) or
too broad (correcting exploratory fishing expeditions alongside
pre-registered tests) — silently changes what "significant" means.
GENEVRA's convention: state the family and the inclusion/exclusion
rationale in the same artifact as the corrected p-values, so it can be
checked rather than assumed.

## Held-out validation

`genevra.population_analysis.temporal_validation` provides two levels,
deliberately labeled by strength:

- `leave_one_seed_out(x_by_seed, y_by_seed)` — a genuine held-out test:
  fits on N-1 seeds' data, checks the discovered relationship's sign on
  the truly unseen Nth seed, repeated for every seed. This is the
  stronger of the two because the held-out fold never touches the
  training data at all.
- `within_seed_holdout(x, y, split_fraction)` — a weaker, always-
  available fallback: fits on one seed's early generations, checks sign
  on that same seed's later generations. Documented as weaker because
  both segments still come from one autocorrelated trajectory, not two
  independent runs.

Both are covered by explicit data-leakage tests
(`tests/test_population_analysis.py`) that construct a case where
leakage would flip the predicted sign and confirm the real
implementation does not leak — see "Insufficient-data handling" below
for how these degrade gracefully rather than fabricating confidence.

## Replication consistency

`genevra.population_analysis.replication_consistency.summarize_replication_consistency(effect_by_seed)`
reports, across independent seeds: `majority_sign`, `agreement_fraction`
(the fraction of seeds whose effect sign matches the majority), and
`sign_reversals`. A low `agreement_fraction` means a heterogeneous,
seed-dependent effect that a pooled p-value alone would hide — RQ4b's
`agreement_fraction=0.5` (12 of 24 sign reversals) is exactly this case:
the near-zero pooled effect reflects genuine seed-to-seed disagreement,
not a real effect masked by noise. A result is never called "replicated"
merely because pooled significance was found.

## Pseudoreplication safeguards

Beyond the replication-unit rule above: `genevra.discovery.replication
.split_seeds` and `genevra.discovery.replication.ReplicationRunner
.evaluate` raise if discovery and validation/replication seed sets
overlap (`docs/statistical_protocol.md`); `genevra.evidence
.validation_split.split_seeds` does the same for the evidence package's
own development/validation seed partition
(`research_evidence/seeds/development_validation_split.json`), checked
by `genevra.evidence.verify.verify_evidence_package`'s
`seed_split_overlap` field.

## Insufficient-data handling

Every statistical function in this project either returns a usable
result or an explicit `None`/`INSUFFICIENT_DATA` state — never a
degenerate number standing in for "not enough data." `permutation_test`
and `cohens_d` require >= 2 observations per sample; the evidence
package's `EvidenceStatus.INSUFFICIENT_DATA` is set whenever a
computation could not run rather than being inferred from a description.
`genevra.ecology.network`'s `EcologicalNetworkAnalyzer` follows the same
rule for interaction-network statistics too small to be meaningful.

## What none of this establishes

A significant permutation test, a large effect size, a tight confidence
interval, or a successful replication is evidence consistent with a
hypothesis under the tested conditions — never proof the underlying
mechanism is real, general, causal, or biologically true. See
`docs/final_research_quality_gate.md` for the project's current, honest
accounting of which findings meet which of these bars, and
`docs/experiment_design.md` for how confounds (like RQ4's) can silently
invalidate an otherwise-correct statistical procedure.
