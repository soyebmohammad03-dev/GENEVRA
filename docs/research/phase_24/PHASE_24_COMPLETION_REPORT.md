# Phase 24 completion report

**Ready for external reproduction on the verified reference platform. Journal submission, recruitment and empirical confirmation remain on hold.** The challenge supports replay of ten public capsule entries and a separate submission path for independent Phase 18 implementations. No external entrant or reviewer participated. No new synthetic campaign or fieldwork was conducted.

## Technical and scientific change

The new challenge CLI verifies the frozen archive, runs the original analyses and separate raw-count checks, then checks its own replicate-level decision aggregation against published CSVs. It computes conditional denominators, Wilson intervals, interval widths and paired Hoeffding contrasts. The archive remains the authority for configuration and observations. Phase 19 envelope inference is reconstructed by its existing separate long-double verifier. The report and figures are written to a new output directory. The exported acquisition package and CSV scorer allow other implementations to participate without editing the frozen benchmark.

The adversarial replay preserved the 180/512 shared-blind false certificates, zero shared-blind coverage, 512/512 abstentions in each asymmetric stale case, and 512/512 abstentions in the missing-stratum and near-threshold cases. The equal-spend envelope had 512/512 coverage under valid large-omission bounds and zero coverage under each invalid-bound stress case. See the [adversarial matrix](ADVERSARIAL.md) and [manuscript update](MANUSCRIPT_UPDATE.md). Those are frozen synthetic outcomes. The new numerical edge cases use deterministic fixtures.

## Validation

The reference machine was a MacBook Air M3 with 8 GiB RAM, macOS 27.0.1 build 26A434, CPython 3.12.15 and uv 0.12.23. The clean environment used pinned arm64 dependencies. The initial end-to-end replay took 136.39 seconds with maximum RSS 396,820,480 bytes and approximately 426 MiB of replay output. It regenerated and matched the published Phase 18 PNG, Phase 19 envelope SVG and identification-floor PNG. The submission smoke check scored all 4,608 deterministic fallback rows and returned null risk among certificates in each case.

A second replay from an export of the staged public tree took 127.79 seconds with maximum RSS 400,801,792 bytes. The [verification receipt](verification-receipt.json) records numerical outcomes and digests. The full local suite passed 1,033 tests in 250.33 seconds with 94% reported coverage, no failures or skips and maximum RSS 229,720,064 bytes. That includes all 20 new scorer tests.

The clean public-tree suite passed 768 tests in 220.93 seconds with 94% reported coverage, no failures or skips and maximum RSS 149,585,920 bytes. The clean tree excludes prior uncommitted local work.

Ruff lint and formatting, strict mypy for the configured source directories, and committed-evidence verification passed. Historical checks found zero changes across 18,143 inventoried files and no CRC failures in 29 historical ZIPs. All 190 preexisting worktree entries were preserved.

The [reproduction guide](REPRODUCE.md) records the commands and exact verification contract. The original capsule excludes some local historical artifacts and older media. Byte-level figure checks target the declared platform. A public score cannot prove an entrant avoided the disclosed target laws. The benchmark does not estimate real-world error rates.

## Decision gates

| Gate | Decision | Evidence or next requirement |
|---|---|---|
| Defensible contribution | PASS | Scoped benchmark and failure cases with an explicit separation of endpoints |
| Frozen reusable benchmark | PASS | Capsule, archived config, acquisition schema, submission protocol and executable score |
| Reproducible principal findings | PASS | Clean internal replay and figure checks |
| Separate verification pathway | PASS | Raw-count estimators and new replicate scorer with distinct code paths |
| Adversarial failure conditions | PASS | Reported frozen counterexamples and focused numerical and input tests |
| Comparison against established methods | CONDITIONAL | Declared baselines and fair access rules in current cases. Need a closer benchmark comparison and variance-aware allocation comparator |
| External-review package | PASS | Phase 23 package plus Phase 24 challenge and instructions. External scrutiny remains pending |
| Empirical validation route | CONDITIONAL | Prospective protocol exists. No qualified custodian, partner, reference assay or approvals |

The new files consist of `scripts/benchmark_challenge.py`, `tests/test_benchmark_challenge.py` and the documentation and manifest in this directory. The root README adds a link. No frozen results, protocols or simulator source were modified.
