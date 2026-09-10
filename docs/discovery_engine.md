# The Discovery Engine (Phase 10)

## What this is, and is not

GENEVRA's discovery engine (`genevra.discovery`) is infrastructure for
**finding and testing potentially interesting phenomena** in stored
experiment results. It is not an LLM chatbot, does not invent random
hypotheses, and never claims to have discovered a scientific truth. Every
component is grounded in structured experimental data a researcher could
inspect directly, and every output carries its own uncertainty and
limitations.

The pipeline: **OBSERVE -> DETECT -> FORMULATE -> TEST -> VALIDATE**,
implemented as:

```
phenomena.py / anomaly.py   -> observed patterns, per run
correlation.py              -> relationships across runs (OBSERVE)
hypothesis.py                -> candidate Hypothesis objects (FORMULATE)
followup.py                  -> ProposedExperiment (a design, not an execution)
loop.py                      -> optional, budget-gated execution + evaluation (TEST)
replication.py                -> independent-seed confirmation (VALIDATE)
contradiction.py             -> conflicting evidence across experiments
memory.py                    -> provenance graph tying it all together
report.py                    -> machine- and human-readable summary
multiple_testing.py          -> FDR correction, used wherever many
                                relationships are scanned at once
```

## Modularity

`genevra.discovery.phenomena.PhenomenonRule` is a protocol; the three
concrete rules shipped (`NoveltyWithoutFitnessGainRule`,
`DiversityCollapseWithContinuedNoveltyRule`, `RepeatedRegimeRule`) are
*examples* from Phase 10.1's list, not the exhaustive set of "discoveries
GENEVRA can make." New rules are added by implementing the protocol, not
by editing `PhenomenonDetector`.

## Execution budget

`genevra.discovery.followup.generate_followup_experiment` only ever
produces a `ProposedExperiment` — a fully specified, `validate()`-able
design. Nothing in this package runs an `EvolutionEngine` on its own
initiative. Actual execution happens only through
`genevra.discovery.loop.run_hypothesis_loop`'s injected
`EvidenceCollector` callables, which a caller controls entirely (e.g. by
wrapping `genevra.analysis.comparison.ComparisonRunner` with its own
generation/seed-count limits).

## Performance

Discovery operates on `ExperimentResult`/`Trajectory`-shaped dicts
already on disk, not on live simulation state — `correlation_discovery`
and `hypothesis` generation consume one scalar summary per run
(`genevra.discovery.correlation.RunSummary`), not raw per-generation
trajectories, so memory scales with the number of runs, not the number
of generations times the number of runs.

See also: `docs/hypothesis_protocol.md` (what a `Hypothesis` means and
how it's evaluated) and `docs/statistical_protocol.md` (multiple
comparisons, effect sizes, the discovery/validation split).
