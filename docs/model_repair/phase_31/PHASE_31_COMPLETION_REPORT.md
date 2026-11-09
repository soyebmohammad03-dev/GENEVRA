# Phase 31 final research and publication gate

**Decision.** Engineering and internal frozen reproduction are complete with documented limitations. The package can be circulated for independent technical reproduction. Journal submission remains on hold.

The seed-zero software example diverged at generation 1 because default elite sorting chose different equal-fitness parents despite identical scores and RNG states. The diagnostic stable rule aligned 15 selection traces and 384 lineage records. Continuous summaries retained small differences and their exact low-level origin is unresolved. The published simulator, benchmark inputs, outputs and scientific claims were left intact.

| Deliverable | Record |
|---|---|
| Numerical diagnosis | [Audit](CROSS_PLATFORM_NUMERICAL_AUDIT.md), [tested contract](REPRODUCIBILITY_CONTRACT.md), [receipt](portability-receipt.json) |
| Scientific audit | [Claim and evidence table](SCIENTIFIC_CLAIM_AUDIT.md) |
| JSS compliance and provenance | [Compliance](JSS_FINAL_COMPLIANCE.md), [encoding inventory](SOURCE_ENCODING_INVENTORY.md), [licensing](LICENSING_AND_PROVENANCE_FINAL.md) |
| Candidate and external challenge | [Artifact inventory](FINAL_ARTIFACT_INVENTORY.md), [reproduction challenge](EXTERNAL_REPRODUCTION_CHALLENGE.md) |
| Decisions | [Readiness matrix](PUBLICATION_READINESS_MATRIX.md), [checksums](SHA256SUMS) |

## Verification

- Clean macOS arm64 worktree, CPython 3.12.15. The full suite collected and passed 835 tests in 144.72 seconds, with zero failures and skips. It includes three new comparator contract tests.
- The separate core wheel and sdist validation ran the pre-contract 832 tests in 147.18 seconds, with zero failures and skips, then removed the installed wheel. The new contract tests passed separately in the wheel test environment.
- The Ubuntu diagnostic used Python 3.12.16 and NumPy 2.5.4. The complete macOS/Ubuntu software installation matrix is in the [Phase 30 platform report](../phase_30/CROSS_PLATFORM_VALIDATION.md). Both new diagnostic policies repeated exactly twice on each platform.
- The frozen replay from a fresh public clone regenerated the original Phase 29 technical PDF and receipt byte for byte in 155.34 seconds. Reported maximum RSS was 378,028,032 bytes. The source archive and its 1,513 members were verified. This replay used existing registered configurations and seeds.
- The separate JSS build used TinyTeX-1 v2026.11, pdfTeX 1.40.29 and the pinned JSS class. All 11 pages were rendered for inspection. The PDF was byte-identical to Phase 29 and contained 12 linked reference destinations.
- Ruff lint and format, strict mypy, shell syntax, relative links, Git whitespace and frozen manifest checks passed. Development used an isolated worktree to preserve local edits and historical material.

The tracked verification commands are `sh scripts/check_distribution.sh 3.12.15 NEW_OUTPUT`, `python -m pytest`, `ruff check .`, `ruff format --check .`, `mypy`, and the [candidate verification commands](EXTERNAL_REPRODUCTION_CHALLENGE.md). The exact diagnostic commands and configuration are in the audit.

The integrated synthetic benchmark and separate numerical reference are the supported contribution. The record supplies no empirical superiority, external endorsement or journal decision. The submission gates remaining are ASCII-specific source and help preparation, author declarations and rights confirmation, and independent reproduction or practical-use evidence.
