# Reproducibility

## Installation

```
pip install -e ".[dev,viz]"
```

`dev` pulls in pytest/ruff/mypy/coverage; `viz` pulls in matplotlib,
required by `genevra.artifacts` (the figure/table system) and therefore
by `reproduce-evidence`. This is the exact command GitHub Actions runs
(`.github/workflows/*.yml`).

## Deterministic seeds

Every stochastic component in GENEVRA takes an explicit seed —
`numpy.random.default_rng(seed)` or, for hierarchical campaign seeding,
`numpy.random.SeedSequence.spawn` (`genevra.campaign.seeding`). There is
no hidden global random state. The same seed, same configuration, and
same code version always produce the same result; this is verified, not
assumed:

- `tests/test_campaign.py::TestCheckpointAndRunner::test_determinism_same_seed_same_result`
  reruns a campaign cell with the same seed and asserts identical output.
- This cleanup session independently reran
  `experiments/exp_ecology_corrected.minimal_competition(0)` twice and
  confirmed byte-identical output
  (`genotypic_diversity=9.443293449034293` both times).
- `genevra.evidence.build.build_evidence_package(scale=FULL)` was run
  twice into separate output directories this session; every generated
  statistics file was byte-identical between the two runs.

Different seeds are checked to actually diverge, not merely assumed to:
`tests/test_campaign.py::TestCheckpointAndRunner::test_different_campaign_seeds_produce_different_seeds`,
and the same manual check above with `--seed 1` producing different
output than `--seed 0`.

## Evidence reproduction

```
python -m genevra.cli reproduce-evidence --mode quick --output <dir>
python -m genevra.cli reproduce-evidence --mode full --output <dir>
```

`--mode full` is the exact command that produced the committed
`research_evidence/` directory (`genevra.evidence.build.build_evidence_package`,
scale `FULL`). `--mode quick` (the default) runs the identical code path
at a much smaller scale, for fast local iteration and CI-style
smoke-checks — same statistics functions, same figure/table/report
generation, only the seed counts and population/generation sizes differ,
and the actual sizes used are always recorded in the output (never
assumed by a reader).

As of this cleanup, `reproduce-evidence` regenerates **all** nine
research questions in the committed package, including RQ4b (the
audit-required same-engine ecology correction) and the
Benjamini-Hochberg FDR family over the package's confirmatory tests —
these are not a separate, undocumented step; `build_evidence_package`
calls `experiments/exp_ecology_corrected.py` and
`genevra.campaign.multiple_comparison.build_multiple_comparison_registry`
directly. Re-running `--mode full` reproduces every number in
`research_evidence/statistics/rq4_corrected.json` and
`rq_family_fdr.json` exactly except the permutation test's own p-value,
which depends on a Monte Carlo random-shuffle seed internal to that
function — the effect size (Cohen's d), sample sizes, and replication
consistency are computed directly from the raw values and reproduce
exactly.

## Evidence verification

```
python -m genevra.cli verify-evidence [research_evidence]
```

Runs `genevra.evidence.verify.verify_evidence_package`, which checks
four things a curated evidence package can silently get wrong:

1. **Checksums** — every file `checksums/manifest.sha256` lists still
   hashes to the recorded SHA-256 digest
   (`genevra.evidence.checksums.verify_checksum_manifest`). The manifest
   format matches the standard `sha256sum` tool's output, so
   `sha256sum -c research_evidence/checksums/manifest.sha256` also works.
2. **Missing referenced files** — every artifact `manifest.json` lists
   actually exists on disk.
3. **Orphaned files** — every file under `figures/`, `tables/`, or
   `reports/` has a corresponding `manifest.json` entry (nothing
   generated without being traced).
4. **Seed-split overlap** — `research_evidence/seeds/development_validation_split.json`'s
   `development_seeds` and `validation_seeds` do not intersect.

This cleanup session independently re-verified the checksum check is
load-bearing, not decorative: deliberately corrupting
`research_evidence/statistics/rq2_sensitivity.json`'s content caused
`verify-evidence` to report `"checksum mismatch"`; restoring the exact
original content returned it to `ok: true`.

## Provenance

Every `EvidenceArtifact` in `manifest.json`
(`genevra.evidence.manifest`) records: `research_question`,
`experiment_id`, `condition`, `seed_set`, `source_data`, `metric_ids`,
`analysis_version`, `config_hash`, `relative_path`, `git_commit`, and
`limitations`. `git_commit` is captured with `git rev-parse HEAD` at
build time (`"unavailable"` if git is not present) — a figure/table/
report generated from a given commit records that commit, so a reader
can check out that exact commit and reproduce it.

## What is committed vs. gitignored

- `research_evidence/` — **committed**. A compact, curated, checksummed
  sample of real generated output (~1MB), not a raw dump.
- `research_artifacts/` — **gitignored** (`.gitignore`). The large,
  uncontrolled scratch tree that `genevra.artifacts.bundle`/
  `genevra.campaign.bundle` write to for one-off local runs; regenerate
  on demand from a stored `ExperimentResult` rather than committing it.
  See `docs/research_artifacts.md`.
- `experiments/results/`, `results/` — gitignored per-experiment scratch
  output (only `.gitkeep` is tracked).
- Standard Python/tooling artifacts (`__pycache__/`, `.venv/`,
  `.mypy_cache/`, `.pytest_cache/`, `.coverage`, `*.ckpt`/`*.npz`/
  `*.npy`/`*.h5`/`*.sqlite`/`*.log`) are gitignored.

## Limitations

- Determinism is verified for GENEVRA's own RNG usage; it does not
  extend to floating-point non-determinism across different NumPy/BLAS
  builds or hardware — all reruns in this project were performed on the
  same machine/environment used to generate the committed package.
- `reproduce-evidence --mode full` takes on the order of a few minutes
  on a laptop (the RQ4b correction's 48 total runs alone took well under
  a minute in this session's timing check) — still small enough that no
  separate "how long will this take" estimate is printed before running,
  unlike the larger `genevra campaign` command
  (`docs/research_campaigns.md`), which does show a budget summary
  before executing.
- Multi-worker parallelism exists in `genevra.campaign.runner.CampaignRunner`
  but is not exercised by `reproduce-evidence`, which always runs
  sequentially — see `docs/phase_17_18_quality_gate.md`.
