# Ecological / Population Statistics: Definitions and Safeguards

Module: `genevra.ecology.competition` (formulas), `genevra.population_analysis`
(replication-unit enforcement).

## The replication-unit rule

**The independent seed/run is the unit of replication for every
cross-condition statistical claim in Phase 15/16.** A single
`ContinuousEvolutionEngine` run produces many organisms, but they share
one environment history, one selection pressure, and downstream RNG
state — they are not independent draws. Every permutation test, Cohen's
d, or bootstrap CI in `genevra.ecology.hypotheses` or
`genevra.population_analysis` is computed over one value per seed, never
one value per organism. `genevra.population_analysis.aggregation`
exists specifically to perform that organism/generation -> seed
reduction before any statistical test runs.

## Formulas used

**Gini coefficient** (`gini_coefficient`, inequality, 0 = equal, 1 =
maximal inequality):

```
G = (2 * sum(i * x_i for i in 1..n, x sorted ascending)) / (n * sum(x)) - (n + 1) / n
```

`None` for fewer than 2 values or an all-zero sample (undefined).

**Pielou's evenness** (`pielou_evenness`, 1 = perfectly even, 0 = one
category dominates):

```
J = H / ln(S)
H = -sum(p_i * ln(p_i) for i in categories with count > 0)
p_i = count_i / total
S = number of non-zero categories
```

`None` for fewer than 2 non-zero categories.

**Herfindahl-Hirschman index** (`herfindahl_index`, concentration,
`1/S` = perfectly even, `1.0` = total concentration):

```
HHI = sum(p_i^2 for i in categories)
```

`None` if the total is 0.

## Insufficient-data behavior

Every function in this area returns an explicit `None` (or, for the
ecology hypothesis tests, an `INSUFFICIENT_DATA` label) rather than a
number computed on too little data:

- correlation/association functions: `None` below 3 paired observations,
  or if either series is constant (matches
  `genevra.analysis.tradeoff.summarize_tradeoff`'s existing convention).
- `EcologicalNetworkAnalyzer`: an explicit insufficient-data result below
  6 nodes / 6 edges.
- `test_ecology_hypothesis`/hypothesis tests generally: `INSUFFICIENT_DATA`
  below `min_seeds` (default 3) per side.
- `leave_one_seed_out`: `agreement_rate=None` below 3 total seeds.

## Multiple comparisons

When many ecology/population hypotheses are tested against the same
stored results (e.g. all of H1-H5, or many pairwise metric
associations), apply `genevra.discovery.multiple_testing.
benjamini_hochberg` to the resulting p-values before treating any as
individually significant — this module does not do that correction
automatically, since it does not know how many comparisons a caller is
running across which analyses.

## What is preserved

Every analysis in `genevra.ecology`/`genevra.population_analysis`
operates on data the caller already has (a stored trajectory, a set of
per-seed values) — none of it discards raw per-seed or per-generation
data as a side effect of computing a summary; the raw inputs remain
whatever the caller passed in.
