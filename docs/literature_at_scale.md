# Literature reproduction at scale (Phase 18)

Builds on `genevra.literature` (Phase 11): a `LiteratureClaim` +
`LiteratureExperimentSpec` + `LiteratureReproductionRunner` triple already
exists per case. Phase 18 adds three things on top, without re-implementing
any of that: reproduction *quality levels*, a *boundary-condition sweep*
over one exposed parameter, and a *comparison matrix* tabulating results.

## Reproduction quality levels

`genevra.literature.quality_levels.ReproductionQualityLevel`:

- `LEVEL_0_CONCEPTUAL` — the case exists and maps variables onto GENEVRA
  constructs; true for every case regardless of outcome (`INCONCLUSIVE`
  results stay at this level — "we could not detect a directional effect
  at this sample size" is not itself a discovered pattern).
- `LEVEL_1_QUALITATIVE` — a statistically detectable, directionally
  interpretable effect exists (`NOT_SUPPORTED` or `CONTRADICTED`: the
  direction is discernible even when it disagrees with the claim or is
  too small to call support).
- `LEVEL_2_QUANTITATIVE` — `SUPPORTED`/`PARTIALLY_SUPPORTED`: a real,
  medium-or-larger (or small-to-medium) Cohen's d in the predicted
  direction.
- `LEVEL_3_MECHANISTIC` — **never auto-assigned.** GENEVRA's reproduction
  runner has no code path that verifies a claimed *mechanism* reproduces,
  only a directional/quantitative pattern; a caller must supply
  `mechanistic_evidence=True` from an actual separate mechanistic study
  (e.g. a causal-chain test from `genevra.mechanisms.causal_chain`) before
  this level is reached.
- `LEVEL_4_ROBUST` — requires >= 2 distinct tested regimes (a real sweep,
  not one point), every regime independently at `LEVEL_2`, and every
  regime meeting the spec's own `replication_required_seeds`.

## Boundary-condition search

`genevra.literature.boundary_search.run_boundary_sweep` takes a
*parametrized* case builder (one exists for CASE A's environmental-change
`period`, added to `case_a_plasticity_evolvability_tradeoff` as a
backward-compatible optional argument) and a list of parameter values,
and runs the full `LiteratureReproductionRunner` at each value. It reports
every point's label plus `.transitions()` — consecutive swept values whose
label differs. It does not decide which transition is "the" boundary;
finding zero transitions (all points land on the same label) is reported
honestly, not treated as a failure to find one.

CLI: `genevra boundary-search --values 5,20,60` (period values, steps per
environmental regime — smaller means faster environmental change).

## Comparison matrix

`genevra.literature.comparison_matrix.ComparisonRow`/`build_comparison_matrix`
tabulate `(LiteratureClaim, ReproductionResult)` pairs into exactly the
columns the spec names (`literature_claim`, `genevra_result`, `direction`,
`effect_size`, `confidence`, `reproduction_level`, `model_mismatch`,
`status`), exported via the existing `genevra.artifacts.tables` CSV/
Markdown helpers — no second table renderer.

## Falsification experiment ranking

`genevra.literature.falsification.rank_falsification_experiments` scores
each generated falsification hypothesis's proposed experiment as
`discriminative_power - 0.3 * normalized_generation_budget`: the mechanism
hypothesis itself gets `discriminative_power=1.0`, every alternative-
confound hypothesis gets `0.6` (it tests a competing explanation, one step
removed from the claim itself). This is a documented heuristic priority
order for a fixed budget, not a claim that the top-ranked experiment *is*
the falsification test — running it and observing its outcome is what
would actually falsify or fail to falsify the claim.

## Known limitations

- Only CASE A currently exposes a sweepable parameter (`period`); CASE
  B/C/D would need the same kind of backward-compatible parametrization
  before a boundary sweep could run on them.
- `LEVEL_3_MECHANISTIC`/cross-case meta-analysis/a general evidence-graph
  extension of `ResearchMemory` beyond its existing record types were not
  built in this phase — `ResearchRecord.record_type` already accepts
  arbitrary new `Literal` values (see `genevra/discovery/memory.py`), and
  extending it with `observed`/`inferred`/`hypothesized` edge-status
  fields is a natural next step, not attempted here to keep this phase's
  scope to what was actually validated end-to-end.
