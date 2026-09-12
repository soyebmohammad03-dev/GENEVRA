# Evolutionary Prediction and Temporal Validation

Module: `genevra.population_analysis.prediction`,
`genevra.population_analysis.temporal_validation`,
`genevra.population_analysis.replication_consistency`.

## Three distinct claims, never conflated

- **Association**: two metrics correlate.
- **Prediction**: an earlier value of one metric correlates with a
  *later* value of another (a lagged relationship).
- **Causal evidence**: an experimental manipulation of one metric changes
  the other, holding confounders constant.

Nothing in this module produces causal evidence. `prediction.py` produces
lagged *association* results; `temporal_validation.py` adds a genuine
train/test split, which is stronger evidence that a *predictive*
relationship generalizes, but is still not a causal claim.

## Lagged prediction (`prediction.py`)

`within_seed_lagged_correlation(predictor, outcome, lag)`: Pearson r
between `predictor[t]` and `outcome[t+lag]` within one seed's own
trajectory. **This is descriptive, not inferential**: generations within
one seed are autocorrelated (the same caveat `genevra.innovation.
activity` already documents), so a single seed's r is one data point,
not a statistically independent finding on its own.

`test_lagged_prediction(predictor_by_seed, outcome_by_seed, lag, rng)`
computes that descriptive r for every seed, then treats the *distribution
of per-seed r values* as the actual inferential object: mean and a
bootstrap CI across seeds (seed is still the unit of replication here,
per `docs/ecological_statistics.md`).

## Temporal cross-validation (`temporal_validation.py`)

Two variants, deliberately kept separate because they answer different
questions:

1. **`within_seed_holdout(x, y, split_fraction)`**: fit a linear
   relationship (`numpy.polyfit`, degree 1) on one seed's early
   generations, check whether the *sign* of the actual x-y relationship
   in that same seed's later (held-out) generations matches the
   train-fit's sign. Weaker — still one autocorrelated trajectory — but
   always available with a single seed.
2. **`leave_one_seed_out(x_by_seed, y_by_seed)`**: fit on N-1 seeds'
   pooled trajectories, check whether the sign holds on the left-out
   seed, repeated for every seed. Requires >= 3 seeds
   (`agreement_rate=None` otherwise) — the genuinely independent-
   replication version of temporal validation.

Neither variant reports an R² or a p-value on the held-out segment; both
report only whether the *sign* of the relationship held, which is a
weaker and more honest claim than a held-out goodness-of-fit number would
imply given GENEVRA's typical seed counts.

## Replication consistency (`replication_consistency.py`)

`summarize_replication_consistency(effect_by_seed)`: given one effect
estimate per independent seed, reports the majority sign,
`agreement_fraction` (fraction of seeds sharing that sign), and
`sign_reversals` (count opposing it). **Pooled significance across seeds
can hide substantial seed-to-seed disagreement** — this report exists
specifically to surface that disagreement rather than let a single
pooled p-value stand in for it. A general-purpose sibling of
`genevra.discovery.replication.ReplicationRunner` (which implements a
discovery/confirmation seed-split protocol for one specific workflow);
this module handles the more common, simpler case of N seeds each
already producing one effect estimate for the same comparison.

## `genevra predict-evolution` / `genevra replication` CLI

Both run small, real scenarios (a `ContinuousEvolutionEngine`'s
population-size series predicting its own mean-energy series; several
seeds' final-population-size change) — illustrative of the mechanism at
laptop scale, not research-grade sample sizes.
