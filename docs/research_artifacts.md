# Research artifact directory (Phase 14.1, 14.9, 14.10)

`genevra.artifacts.bundle.generate_artifact_bundle(result, output_root, ...)`
writes a standard, reproducible tree for one stored `ExperimentResult`:

```
research_artifacts/<experiment_id>/
    raw_data/
    derived_data/
    metrics/
    figures/
    tables/
    reports/
    provenance/
    configurations/
    seeds/
    logs/
    supplementary/
```

`experiment_id` is `"<name>_seed<seed>"`. `raw_data`/`derived_data`/
`metrics`/`logs`/`supplementary` are created but not yet populated by
`generate_artifact_bundle` in this phase — they exist so future work
(e.g. dumping intermediate mutational-landscape samples, or an
experiment's raw per-organism observations) has a defined home without
inventing a new directory convention later.

## Do not commit this directory

`research_artifacts/` is listed in `.gitignore`. Everything under it is
reproducible generated output — regenerated on demand from a stored
`ExperimentResult` JSON — never a second source of truth. Commit source
code, docs, and small test fixtures; never commit a generated bundle.

## Provenance (Phase 14.1's "traceable to...")

`ArtifactDirectory.write_provenance(...)` writes:

- `provenance/provenance.json` — `experiment_id`, `seeds`,
  `configuration` (name/condition_id/environment_summary/software from
  the stored result), `git_commit` (best-effort `git rev-parse HEAD`),
  `metric_version`, `analysis_version`, `created_at`.
- `seeds/seeds.json` — the seed list, standalone, for quick inspection
  without parsing the full provenance record.
- `configurations/configuration.json` — the same configuration dict,
  standalone.

Every figure's own `<figure_id>.json` sidecar (see
`docs/figure_system.md`) independently repeats its `experiment_id` and
`git_commit`, so a figure found in isolation is still traceable back to
its run without needing the directory's `provenance.json` alongside it.

## Report bundle (Phase 14.10)

`generate_artifact_bundle` also writes `reports/report.json` and
`reports/report.md` — a `genevra.artifacts.report.ArtifactReportBundle`
covering (per Phase 14.10's 15-point list): research question,
conditions/seeds, metrics/statistical methods, main results, figures,
tables, alternative explanations, limitations, reproduction status,
replication status, open-endedness evidence, and a scientific-language
safeguards statement. A single-run bundle honestly reports "n/a" for
reproduction/replication/open-endedness sections it did not evaluate
rather than fabricating a status.

## Research artifact index (Phase 14.9)

`genevra.artifacts.index.build_index` — not a graphical dashboard, per
the spec's explicit instruction — produces a
`ResearchArtifactIndex` (experiment/condition/seed counts, successful vs.
failed run counts, phenomena/hypothesis/replication counts from
`ResearchMemory` when supplied, figure/table counts, quality-gate
status), both as a dict (`to_dict()`) and human-readable text
(`to_text()`). It never inspects the filesystem to guess counts; every
number comes from the caller-supplied results list / `ResearchMemory`.

## Tables

`genevra.artifacts.tables` writes CSV, Markdown, and a minimal LaTeX
`tabular` environment from plain row dicts — every row-building function
(`experiment_summary_rows`, `failed_run_rows`) includes failed/extinct
runs, never drops them (Phase 14's "do not hide failed runs").

## CLI

```
genevra tables <result_path_or_dir> --output-dir tables/
genevra artifacts <result_path> --output-root research_artifacts --question "..."
genevra report <result_path> --output-root research_artifacts [--output report.json]
```

`artifacts` prints the generated directory tree; `report` prints (or
writes) just the report text/JSON. Both call the same
`generate_artifact_bundle` under the hood — they differ only in what the
CLI surfaces, not in what gets written to disk.

## Reproducibility test

`tests/test_artifacts_integration.py::test_full_artifact_bundle_reproducibility`
runs a real tiny experiment, saves it, generates the full bundle, and
asserts every figure/table/provenance/report file exists and cross-
references the same `experiment_id` and seed set — GENEVRA's core
research-artifact-reproducibility check (Phase 14.12).
