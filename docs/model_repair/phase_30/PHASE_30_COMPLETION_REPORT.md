# Phase 30 distribution and software quality closure

The wheel regression is closed. The previous 26 failures came from a repository-relative runtime resource assumption. All 26 are covered by the unchanged tests and the full installed-package runs. The source distribution builds the same runtime resources, the editable workflow remains supported, and the wheel excludes frozen archives and datasets.

| Deliverable | Evidence |
|---|---|
| Install, run, verify, and remove | [Installation validation and user guide](INSTALLATION_VALIDATION.md) |
| Individual disposition of previous wheel failures | [Wheel compatibility report](WHEEL_COMPATIBILITY_REPORT.md) |
| Platform environments and exact test records | [Cross-platform validation](CROSS_PLATFORM_VALIDATION.md) |
| Encoding and command-help inventory | [Source audit](ASCII_SOURCE_AUDIT.md) and [documentation audit](DOCUMENTATION_AUDIT.md) |
| License and redistribution boundaries | [Licensing audit](LICENSE_AND_REDISTRIBUTION_AUDIT.md), [Python 3.11 receipt](distribution-macos-py311.json) and [Python 3.12 receipt](distribution-macos-py312.json) |
| Source and provenance changes | [Software quality audit](SOFTWARE_QUALITY_AUDIT.md) |
| Frozen artifacts, archived raw inputs and publication render | [Integrity record](FROZEN_EVIDENCE_INTEGRITY.md) |

## Engineering changes and commands

Hatchling now copies three existing scripts into the wheel. The loader uses `importlib.resources` and a fixed allowlist. A source-tree fallback uses the checkout that supplied the package. Figure, campaign and evidence provenance use the same checkout-derived revision logic. The only user-visible CLI changes are the resource and optional dependency diagnostics, the comparison command's source boundary, and truthful revision metadata. The three new regression tests cover invalid resource names, missing resources and unavailable standalone revision attribution. The underlying model and experiment definitions remain byte-identical.

```sh
uv build --out-dir NEW_DIST
ruff check .
ruff format --check .
mypy
sh -n scripts/check_distribution.sh
git diff --check
sh scripts/check_distribution.sh 3.11 NEW_OUTPUT_311
sh scripts/check_distribution.sh 3.12 NEW_OUTPUT_312
sh scripts/reproduce_final_research.sh --publication-only NEW_RENDER
(cd docs/model_repair/phase_30 && shasum -a 256 -c SHA256SUMS)
```

The wheel test runners use `python -I -m pytest` against the tracked tests from a directory outside the checkout. The editable suite uses `python -m pytest` in a fresh public checkout. Local Ruff 0.17.3 and mypy 2.4.1 passed. Publication-only reproduction starts from the frozen evidence and performed no campaign. The raw archive's 1,513 members were independently checked against its internal manifest.

The exact source inventory includes the project README and build metadata, the distribution workflow and two checks, the runtime resource loader and provenance helper, their CLI/evidence/artifact/campaign consumers, one regression test file, and the Phase 30 records. See the [research branch](https://github.com/soyebmohammad03-dev/GENEVRA/tree/research/publication-development) for the committed diff. The original checkout's local historical files and in-progress model edits were kept separate.

## Decision

The wheel and source distribution support the tested installed workflows. The software phase provides a documented baseline for future submission work. The JSS-specific ASCII source conversion, any additional formatted reference coverage, author declarations, and rights for repackaging the historical supplement remain open. External reproduction and evidence of practical value still require independent researchers. The phase provides no new validation of the research claims and no editorial decision.
