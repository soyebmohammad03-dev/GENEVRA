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
  8 seeds.

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
  actual `evidence_status`. One (RQ4, ecology) is `SUPPORTED` with a
  large, statistically significant effect; several others are
  `INCONCLUSIVE`, `NOT_SUPPORTED`, or `INSUFFICIENT_DATA`. All are
  preserved deliberately; see `reports/negative_and_inconclusive_results.md`
  and `docs/final_research_quality_gate.md`.

## Research questions covered

See `tables/research_question_matrix.md` for the master table (RQ,
hypothesis, experiment, seeds, primary metric, statistical plan,
status). RQ1-RQ8 are the questions named in the Phase 19 spec; **not all
eight have equally strong evidence** — several are `INSUFFICIENT_DATA`
or `INCONCLUSIVE` at this sample size, and that is reported honestly
rather than adjusted. Only CASE A of GENEVRA's four literature cases
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
