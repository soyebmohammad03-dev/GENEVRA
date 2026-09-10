# Hypothesis Protocol (Phase 10)

## What a `Hypothesis` is

`genevra.discovery.hypothesis.Hypothesis` is a candidate statement about
a relationship between two variables (`independent_variable`,
`dependent_variable`, an optional `predicted_direction`), always carrying
`supporting_observations`, `conflicting_observations`,
`source_experiment_ids`, and an `evidence_score` — never presented as
established truth. Its `note` field says so explicitly.

Generation is deterministic and rule-based (`hypotheses_from_correlations`,
`hypotheses_from_recurring_phenomena`) — **no external LLM is used or
required**. Templates:

- *From a correlation*: "If X changes consistently with Y, investigate
  whether X predicts Y" — only emitted when the correlation clears both
  an FDR-corrected significance threshold and a minimum effect size
  (`effect_size_threshold`), never from a q-value alone.
- *From a recurring phenomenon*: "If phenomenon P recurred across >= N
  independent seeds in experiment E, test whether it persists under
  further independent seeds" — a single-seed observation never generates
  a hypothesis on its own.

## From hypothesis to follow-up experiment

Every `Hypothesis` can be turned into a `genevra.discovery.followup
.ProposedExperiment` — independent/dependent variables, controls,
conditions, seed policy, sample size, generation budget, an analysis
plan, expected outcomes per label, and possible confounds.
`ProposedExperiment.validate()` checks the *design* is well-formed (e.g.
enough seeds, at least two conditions); it says nothing about whether the
hypothesis itself is correct. **A proposed experiment is never
auto-executed.**

## Evaluation labels

`genevra.discovery.loop.evaluate_hypothesis` assigns exactly one of four
labels, each with an explicit, checkable criterion — never "proven":

| Label | Criterion |
|---|---|
| `insufficient_evidence` | No replication evidence yet, or fewer than `min_independent_seeds` independent seeds in it. |
| `supported` | Replication's bootstrap CI excludes zero, and its sign matches `predicted_direction` (or the original evidence's sign, when no direction was predicted). |
| `contradicted` | Replication's CI excludes zero, but the sign disagrees. |
| `inconclusive` | Enough seeds were gathered, but the CI still includes zero — evidence for *no distinguishable effect at this sample size*, not evidence the hypothesis is false. |

`replicated` in `genevra.discovery.replication.ReplicationResult` is a
necessary check for `supported`, never proof the underlying effect is
real or will hold under yet more seeds — see `docs/statistical_protocol.md`.

## Contradictions

`genevra.discovery.contradiction.find_contradictions` flags when two
experiments report opposite-signed, non-trivial correlations for the
same variable pair. It never resolves the disagreement — it is a
candidate for replication or closer inspection of differing conditions,
recorded exactly as `Contradiction`, not adjudicated automatically.
