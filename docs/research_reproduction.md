# Literature Reproduction (Phase 11)

This document describes `genevra.literature`: a framework for encoding a
published evolutionary claim as an explicit, falsifiable experiment
specification, running it under GENEVRA's own model assumptions, and
reporting the result with a computed label — never a hard-coded
scientific conclusion.

## Why this exists

GENEVRA's organism/environment/learning model is its own thing, not a
faithful reimplementation of any published model. Testing "does GENEVRA
show the qualitative pattern paper X describes?" is a legitimate, useful
question. Claiming "GENEVRA reproduced paper X's experiment" is not,
unless the model assumptions genuinely match — and for every case shipped
so far, they do not exactly match. This module exists to make that
distinction impossible to lose: every report generated here states both
things, and never conflates them (see "Reproduction vs. replication"
below).

## Core types

- `genevra.literature.claims.LiteratureClaim` — a structured record of a
  paper's claim: research question, claim text, independent/dependent
  variable, environmental regime, organism/evolutionary assumptions,
  measurement definition, expected direction, known limitations, and a
  `genevra_mapping` field that must state, in prose, how (and how
  approximately) the claim's variables map onto GENEVRA's model. Never
  asserts the claim is true — it is a hypothesis structure, not a
  conclusion.
- `genevra.literature.spec.LiteratureExperimentSpec` — a fully
  serializable (JSON) experiment design: control/treatment condition
  names, population size, generations, seeds, and — critically —
  `primary_metric`, `statistical_test`, and `expected_direction`, all
  **locked in before any run happens** (see "Avoiding circular
  reasoning"). The condition factories themselves are ordinary Python
  callables (`ConditionFactory = Callable[[int], ExperimentConfig]`),
  exactly like every other GENEVRA experiment in this repo — not
  serialized, only referenced, following the same reproducibility
  contract (config + seed + version-controlled code) every other
  experiment here already relies on.
- `genevra.literature.runner.LiteratureReproductionRunner` — loads a
  spec, runs its two conditions via the existing
  `genevra.analysis.comparison.ComparisonRunner` (no experiment-execution
  code is duplicated here), extracts the pre-registered primary metric
  from each run's final generation (`extract_metric`, which supports
  dotted/indexed paths like `"fitness_summary.mean"` or
  `"learning_gene_stats.1.mean"`), and classifies the evidence
  (`classify_evidence`) into one of six labels.

## Result labels

| Label | Meaning |
|---|---|
| `INVALID_EXPERIMENT` | The comparison itself failed validation (`ComparisonValidation`) or too few runs completed to compute anything. |
| `INCONCLUSIVE` | The permutation test does not reject the null at the spec's confidence level — no distinguishable effect at this sample size. |
| `NOT_SUPPORTED` | A statistically detectable difference exists, in the predicted direction, but Cohen's d < 0.2 (negligible). |
| `PARTIALLY_SUPPORTED` | Significant, predicted direction, 0.2 <= |d| < 0.5. |
| `SUPPORTED` | Significant, predicted direction, |d| >= 0.5. |
| `CONTRADICTED` | Significant, but in the direction opposite the claim's prediction. |

`"confirmed"` is never used anywhere in this module. Every label is
computed from `genevra.analysis.aggregation.permutation_test` and
`cohens_d` — the same statistical primitives used throughout GENEVRA,
not a new inference method introduced for this phase.

## Avoiding circular reasoning

`LiteratureExperimentSpec.primary_metric`, `.statistical_test`, and
`.expected_direction` are set when the spec is authored (see
`genevra.literature.cases`), before `LiteratureReproductionRunner` ever
sees a result. There is no code path in `classify_evidence` or `run()`
that inspects multiple candidate metrics and picks whichever one "worked"
— the metric is fixed input, not a search variable. If a researcher wants
to explore other metrics after seeing a result, that is a legitimate
*exploratory* follow-up, but it must be recorded as a new spec (a new
`spec_id`), never as a silent edit to the spec that already produced a
confirmatory label.

## Alternative explanations and falsification

`genevra.literature.alternative_explanations.standard_alternative_explanations`
generates one `AlternativeExplanation` per standard confound (mutation
rate, population size, environmental volatility/predictability, cue
reliability, lineage history, survival bias, baseline fitness, metric
definition, stochastic variation) for any observed
independent-variable/dependent-variable association. Every explanation
starts `status="untested"` — this module never resolves which explanation
is correct; it only names the discriminating experiment and required
control that *would* distinguish it.

`genevra.literature.falsification.generate_falsification_hypotheses`
turns an observation into H1 (the claimed mechanism) plus one competing
`Hypothesis` per standard confound, reusing
`genevra.discovery.hypothesis.Hypothesis` and
`genevra.discovery.followup.generate_followup_experiment` rather than a
parallel representation — a falsification hypothesis is evaluated through
the exact same `genevra.discovery.loop.evaluate_hypothesis` machinery as
any other GENEVRA hypothesis.

## Provenance

`genevra.literature.registry` stores every claim and reproduction result
as records inside the existing `genevra.discovery.memory.ResearchMemory`
— `"literature_claim"` and `"reproduction_result"` record types (added to
`ResearchMemory.RecordType`), linked by `parent_ids` — rather than a
second, disconnected provenance store. `config_hash` gives a short,
deterministic hash of a spec's full configuration for exact-rerun
verification.

## Reproduction vs. replication — a note on vocabulary

This module's reports distinguish two claims that are easy to conflate:

- **"GENEVRA reproduced the qualitative pattern."** The tested metric
  moved in the predicted direction under GENEVRA's own model. This is the
  strongest claim any `ReproductionReport` ever makes, and only when the
  label is `SUPPORTED` or `PARTIALLY_SUPPORTED`.
- **"GENEVRA reproduced the original experiment."** This would require
  GENEVRA's organism, environment, and evolutionary dynamics to match the
  source paper's model — which none of the four initial cases claim (see
  each case's `known_limitations` and `approximation_notes`). This report
  never makes this claim.

## The four initial cases

`genevra.literature.cases` ships four case factories
(`case_a_plasticity_evolvability_tradeoff`,
`case_b_volatility_and_plasticity`, `case_c_history_dependence`,
`case_d_learning_strategy_predicts_potential`), inspired by (not copies
of) Cuypers, Rutten & Hogeweg (2017) and Jorritsma & van den Berg (2026).
**Every case documents its approximations explicitly** in
`LiteratureClaim.known_limitations` and
`LiteratureExperimentSpec.approximation_notes` — see each case's
docstring in `src/genevra/literature/cases.py`. Notably:

- Neither paper's gene-regulatory-network model exists in GENEVRA;
  "evolvability"/"plasticity" are approximated by GENEVRA-native
  quantities (`genotypic_diversity`, the heritable `plasticity_gate`
  learning gene).
- Case C's contingency claim is properly about *variance* of outcomes
  across replicate histories; `LiteratureReproductionRunner` only
  implements a mean-difference test, so Case C tests a weaker,
  mean-based proxy — documented, not silently substituted.
- Case D's "future evolutionary potential" is approximated by
  `behavior_centroid_shift` late in the run, not a proper re-measured
  evolvability/held-out-shift definition.

## CLI

```bash
genevra literature                       # list the four cases
genevra reproduce case_a --population-size 16 --generations 20 --seeds 8
genevra falsify plasticity novelty --observed-direction positive
```

Both `reproduce` and `falsify` support `--output <path.json>` for
machine-readable output; without it, they print the human-readable text
report.
