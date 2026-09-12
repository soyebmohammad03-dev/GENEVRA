# The Research Evidence Package (Phase 19)

`research_evidence/` is a small, curated, **committed** directory of
real GENEVRA output — figures, tables, statistics, and reports actually
produced by running GENEVRA's experiment and analysis machinery, kept
under version control so a reader can inspect concrete evidence rather
than only claims about what GENEVRA can generate.

This is a genuinely different policy from every other generated-output
directory in this project. `research_artifacts/` (Phase 14/17) is
large, reproducible, and gitignored — regenerate it on demand from a
stored `ExperimentResult` or `CampaignConfig`, never commit it.
`research_evidence/` is small (well under 1 MB), curated by hand for
what it includes and omits, and committed deliberately.

## Structure

```
research_evidence/
    README.md                 <- what this package is, exact reproduction command
    manifest.json              <- one EvidenceArtifact record per figure/table/report/data file
    research_questions/        <- one ResearchQuestion JSON per RQ1-RQ8
    experiments/                (reserved; case configs live under configurations/ this round)
    data/                       compact raw-data samples (not every seed's full trajectory)
    metrics/                    the unified metric registry
    statistics/                 computed statistics behind each research question
    figures/                    PNG + JSON metadata sidecar per figure
    tables/                     CSV + Markdown tables
    reports/                    one Markdown report per RQ, plus the negative-results report
    provenance/                 (reserved for future campaign-level provenance)
    configurations/             frozen experiment specs
    seeds/                      seed lists, including the development/validation split
    supplementary/              (reserved)
    checksums/manifest.sha256   SHA-256 over every file above
```

## Generating and verifying it

```
python -m genevra.cli reproduce-evidence --mode full --output research_evidence
python -m genevra.cli verify-evidence research_evidence
```

`--mode quick` (the CLI default) runs the identical code path at a much
smaller scale — useful for fast local iteration and for this project's
own test suite, never used to generate the checked-in package.

`genevra.evidence.build.build_evidence_package` is the single function
both commands and the checked-in package go through — there is no
separate "demo" code path that differs from what actually ran.

## What `verify-evidence` checks

Implemented in `genevra.evidence.verify.verify_evidence_package`:

1. **Checksum integrity** — every file `checksums/manifest.sha256` lists
   still hashes to the recorded SHA-256 digest.
2. **Reference validity** — every `EvidenceArtifact.relative_path` in
   `manifest.json` points at a file that actually exists.
3. **No orphans** — every file under `figures/`, `tables/`, or
   `reports/` has a corresponding manifest entry.
4. **No seed-split overlap** — `seeds/development_validation_split.json`'s
   `development_seeds` and `validation_seeds` do not intersect.

A corrupted or hand-edited file, a manifest entry pointing at a deleted
file, or an unreferenced figure dropped into `figures/` are all real,
independently tested failure modes (see `tests/test_evidence.py`), not
theoretical checks.

## Honesty conventions carried over from every prior phase

- Every number in `research_evidence/` traces to a real run; nothing is
  hand-typed. See `docs/final_research_quality_gate.md` for what the
  evidence actually does and does not show.
- Negative and inconclusive results are preserved, not filtered —
  `reports/negative_and_inconclusive_results.md` lists every research
  question that did not resolve to a clean supporting result.
- `EvidenceStatus` uses the same cautious vocabulary as
  `genevra.literature.runner.ReproductionLabel`
  (`SUPPORTED`/`PARTIALLY_SUPPORTED`/`INCONCLUSIVE`/`NOT_SUPPORTED`/
  `CONTRADICTED`/`INSUFFICIENT_DATA`/`NOT_TESTED`) — never "confirmed"
  or "proven."

## Known gaps

- Only 1 of GENEVRA's 4 literature cases (CASE A) is represented.
- No `CampaignMode.RESEARCH`-scale (20+ seed) run is included — every
  research question here used 3-10 seeds/genomes, documented per-RQ.
- The development/validation seed split (Phase 19.4) is a real,
  non-overlapping partition of the seeds actually used, but the
  analysis choices in `genevra.evidence.build` (lag `k`, status
  thresholds) were fixed in code rather than formally re-derived from
  a development-only subset before the split existed — see
  `docs/final_research_quality_gate.md` question 20.
