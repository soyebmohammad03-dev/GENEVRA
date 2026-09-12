# GENEVRA Research Evidence Package

This directory is **curated, committed evidence** — a compact, real
sample of what GENEVRA's experiment/analysis machinery produces — not a
raw experiment dump (those stay in the gitignored `research_artifacts/`
scratch tree; see `docs/research_artifacts.md`) and not a second
simulation engine. Every number here traces to an actual run executed by
`genevra.evidence.build.build_evidence_package`.

## What generated this

```
python -m genevra.cli reproduce-evidence --mode full --output research_evidence
```

`--mode full` is what produced the files checked into this directory:

- CASE A (literature reproduction, plasticity/evolvability under a
  changing environment): 8 seeds, population 16, 15 generations, both
  `no_learning` and `evolvable_learning` conditions.
- Boundary-condition sweep over CASE A's environmental-change period:
  4 seeds, population 12, 10 generations, periods `[10, 20, 40]`.
- Robustness/evolvability sampling: 10 independently sampled genotypes
  (one per seed 0-9).
- Ecology (isolated vs. shared, via `experiments/exp1_isolated_vs_shared.py`):
  8 seeds. **An independent audit (2026-09-13) found this comparison
  CONFOUNDED** — it changes the simulation engine (discrete
  `EvolutionEngine`+`GridWorld` vs. continuous
  `ContinuousEvolutionEngine`+`SharedGridWorld`), the generation
  structure, the selection mechanism, and the sensory input
  dimensionality (`channels=2` vs. `3`) alongside ecology, so its
  statistic cannot be attributed to ecological interaction structure
  alone. The original numbers are real and preserved
  (`research_questions/RQ4.json`, `reports/RQ4.md`); only their
  interpretation as ecological evidence is withdrawn.
- **RQ4b (audit-required same-engine correction)**, via
  `experiments/exp_ecology_corrected.py`: both conditions use
  `ContinuousEvolutionEngine`+`SharedGridWorld` with identical
  architecture/config; only `resource_a_density` (competition intensity
  for a shared resource) differs — 0.30 (`minimal_competition`) vs. 0.05
  (`shared_competition`). 24 seeds per condition (exceeding the
  pre-registered 20-seed minimum in
  `configurations/rq4_corrected_analysis_plan.json`, frozen to disk
  *before* the experiment ran). Result: Cohen's d = -0.10, raw
  permutation p = 0.7303, Benjamini-Hochberg-adjusted p = 0.8171 (a
  2-test confirmatory family with the CASE A test —
  `statistics/rq_family_fdr.json`), status **NOT_SUPPORTED**. This is a
  genuine, well-powered null: `agreement_fraction=0.5` across seeds (12
  of 24 sign reversals) shows individual seeds are honestly split on
  direction, not a real effect masked by noise. It tested exactly one
  ecological parameter against one metric — it does **not** establish
  that ecology "generally" has no effect on evolutionary dynamics; see
  `tables/rq4_historical_vs_corrected.md` for the original-vs-corrected
  comparison and `reports/RQ4b.md` for the full limitations.

`--mode quick` (the CLI's default) runs the identical pipeline at a much
smaller scale for fast iteration and CI-style checks — the same code
path, smaller sample sizes, always self-reporting the exact sizes used.

## Verifying this package

```
python -m genevra.cli verify-evidence research_evidence
```

Checks SHA-256 checksums (`checksums/manifest.sha256`) against the files
on disk, that every artifact `manifest.json` references actually exists,
that no figure/table/report under `figures/`, `tables/`, or `reports/`
is missing a manifest entry (no orphans), and that the development/
validation seed split has no overlap.

## What is and is not here

- `data/case_a_raw_sample.json` keeps only the **first 2 of 8 seeds**
  per condition's full trajectory, not all 8 — the rest are reproducible
  from the command above rather than duplicated on disk. This is
  documented, not silently omitted (Phase 19.31).
- `figures/` holds compact PNGs (~150 DPI, matplotlib's default scientific
  style from `genevra.artifacts.style`) plus a JSON metadata sidecar per
  figure (figure ID, data source, metrics, git commit, caption,
  limitations) — no SVG/PDF duplicates, to keep this directory small.
- Every `research_questions/RQ*.json` and `reports/RQ*.md` states its
  actual `evidence_status`. RQ4 (the original ecology comparison) is
  `CONFOUNDED` — a real, reproducible statistical difference that
  cannot be attributed to ecology alone; its same-engine correction,
  RQ4b, is `NOT_SUPPORTED`. The rest are `INCONCLUSIVE`,
  `NOT_SUPPORTED`, or `INSUFFICIENT_DATA`. **No research question in
  this package currently has unconfounded, validated SUPPORTED
  evidence.** All statuses are preserved deliberately; see
  `reports/negative_and_inconclusive_results.md`,
  `tables/rq4_historical_vs_corrected.md`, and
  `docs/final_research_quality_gate.md`.

## Research questions covered

See `tables/research_question_matrix.md` for the master table (RQ,
hypothesis, experiment, seeds, primary metric, statistical plan,
status). RQ1-RQ8 are the questions named in the Phase 19 spec, plus RQ4b
(the audit-required same-engine correction of RQ4, added 2026-09-13);
**not all of them have equally strong evidence** — several are
`INSUFFICIENT_DATA` or `INCONCLUSIVE` at this sample size, and that is
reported honestly rather than adjusted. Only CASE A of GENEVRA's four
literature cases
(A/B/C/D) is represented in this evidence package; B/C/D remain
untested here (the machinery exists in `genevra.literature.cases`, it
was not re-run at evidence-package scale this session — a scope
reduction, not a capability gap).

## Limitations

See `docs/final_research_quality_gate.md` for the full, self-critical
accounting. In short: every result here comes from one relatively small
(laptop-feasible) run of GENEVRA's own model, not a large-scale study,
not an independent biological replication, and not a claim that any
literature paper has been proven right or wrong.
