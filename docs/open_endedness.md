# Open-Endedness (Phase 12)

`genevra.analysis.open_endedness` (Phase 8) already assembled novelty,
diversity, evolvability, and stagnation trends into one
`OpenEndednessReport`, explicit that it never emits a single
"OPEN_ENDED = True/False" verdict. Phase 12 (`genevra.innovation`)
upgrades this into a multi-dimensional diagnostic framework, inspired by
— but not a copy of — the MODES framework (Dolson et al. 2019), while
keeping GENEVRA's own mechanistic (lineage/strategy-based) focus.

**This module never declares GENEVRA "fully open-ended."** Every report
it produces states this explicitly (see `OpenEndednessLabReport`'s
`not_a_verdict_note`, printed in every `to_text()` output).

## Measurement architecture

`genevra.innovation.analyzer.OpenEndednessAnalyzer` composes independent,
individually-enabled measurements (`OpenEndednessAnalyzerConfig`):

| Measurement | Field | Module |
|---|---|---|
| Base novelty/diversity/evolvability trends, stagnation | `base`, `stagnation` | `genevra.analysis.open_endedness`, `genevra.analysis.stagnation` (reused, not reimplemented) |
| Innovation events | `innovation_events` | `genevra.innovation.events` |
| Evolutionary activity (lineage/strategy persistence, turnover) | `activity` | `genevra.innovation.activity` |
| Trajectory shape classification | `trajectory` | `genevra.innovation.trajectory` |

Each is versioned in `MEASUREMENT_VERSIONS`. **These are not claimed to be
equivalent aspects of one thing** — they are separate observables that
happen to be assembled into one report for convenience, not one combined
score.

## Trajectory shape classification

`genevra.innovation.trajectory.classify_metric_trajectory` labels a
metric's finite observed series as one of:

- `sustained_increase` / `sustained_decrease` — a clear linear trend
  (`genevra.analysis.stagnation._trend_slope`, the same transparent
  least-squares method used throughout GENEVRA) with no detected change
  point.
- `plateau` — trend magnitude below `flat_threshold` and no change point.
  Explicitly: "no evidence of continued change within the tested
  horizon — a longer run could still resume changing."
- `oscillating` — the windowed trend reverses sign repeatedly (reusing
  `genevra.discovery.phenomena.RepeatedRegimeRule`'s exact heuristic, not
  a second implementation of "oscillating").
- `regime_shift` — one or more statistically significant change points
  detected via `genevra.analysis.regime_detection.detect_change_points`
  (permutation-tested CUSUM-style segmentation, already used for Phase 9's
  evolutionary-transition detection).

Every label carries a fixed interpretation note (`_SHAPE_NOTES`); none
of them says or implies "proven open-ended."

## Phase-space analysis

`genevra.innovation.phase_space` builds a `PhaseSpaceTrajectory` from any
set of named per-generation metric series (fitness, diversity, novelty,
innovation rate, etc.) and, optionally, projects it via
`project_phase_space` — mean-centered PCA computed with
`numpy.linalg.svd` (no new dependency, no scikit-learn). The projection
result always reports its `method` string and
`explained_variance_ratio`; dimensionality reduction is never presented
without that context.

## Potential vs. realized innovation

`genevra.innovation.potential_vs_realized` keeps two measurements
structurally separate:

- **Realized**: what the trajectory actually shows
  (`instantaneous_novelty`, already computed every generation).
- **Potential**: what a single-mutation-step sample around genotypes at
  that generation could reach
  (`genevra.metrics.evolvability.EvolvabilityAnalyzer.mean_behavioral_distance`,
  gathered via
  `genevra.analysis.evolvability_over_time.sample_evolvability_over_generations`).

`build_potential_vs_realized_report` pairs the two series at shared
generations and reports `realized_minus_potential_mean` plus a
**descriptive** `sign_agreement_fraction` — never a correlation p-value,
because per-generation values within one run are autocorrelated, not
independent samples (the same pseudoreplication concern documented in
`genevra.discovery.correlation`). Potential is never assumed to become
realized; a large gap in either direction is reported, not resolved.

## Research quality gates

`genevra.innovation.quality_gates.evaluate_quality_gates` checks a
result's stated facts (`QualityGateInputs`) against a configurable set of
gates (`QualityGateConfig`) — sufficient independent seeds, predefined
primary metric/comparison, reproducible seeds, successful completion, no
unexplained missing data, statistical test/effect size/uncertainty
computed, multiple-testing correction where relevant, independent
replication, held-out validation, complete provenance. Every gate can be
disabled (`require_*=False`) when it is scientifically inappropriate for
a given experiment (e.g. a single pre-registered comparison does not need
multiple-testing correction) — this module never forces one fixed
checklist onto every experiment.

## CLI

```bash
genevra open-endedness results/run.json   # full lab report
genevra innovation results/run.json        # innovation events + dependency graph only
genevra activity results/run.json          # evolutionary activity only
```

All three accept `--output <path.json>` for machine-readable output.

## What this module does not establish

- That GENEVRA satisfies any particular formal definition of open-ended
  evolution from the literature — no such definition is operationalized
  here as a pass/fail test.
- That a trend observed within a finite run would continue indefinitely,
  or that a plateau observed late in a run could never resume changing
  under more generations or a different environment.
- That any measurement here generalizes beyond the specific environment
  configuration and lineage history it was computed on (see "Environment
  / Lineage Dependence" in every generated `OpenEndednessLabReport`).

See `docs/innovation.md` for the innovation-event/dependency-graph half
of this framework in detail.
