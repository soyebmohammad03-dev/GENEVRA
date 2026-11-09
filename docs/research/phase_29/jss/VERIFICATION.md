# Internal verification record

The frozen benchmark and technical review inputs were replayed from public research commit `85d1597cc30adf5e47dacea5a4aa0d2f43553a3e`. The JSS preparation files were then staged in the clean clone to check the separate typesetting workflow.

- Platform: macOS 27.0.1 build 26A434, arm64, CPython 3.12.15, uv 0.12.23 and NumPy 2.5.4.
- Installation: the 49 locked dependencies and GENEVRA 0.1.0 installed in a fresh virtual environment. `uv pip check` reported all 50 packages compatible before installing the optional test plugin. The documented workflow uses an editable install from the public checkout.
- Documentation commands: `genevra --help`, `genevra verify-evidence research_evidence`, `python -m pydoc genevra.analysis.coverage_envelope`, and `python scripts/benchmark_reference.py --help` succeeded.
- Worked example: `sh scripts/reproduce_final_research.sh --publication-only NEW_OUTPUT` regenerated the original Phase 29 PDF and receipt byte for byte.
- Full replay: `/usr/bin/time -lp sh scripts/reproduce_final_research.sh NEW_OUTPUT` verified the downloaded archive and file manifest, replayed the archived benchmark, checked the reference results and reproduced the original publication outputs byte for byte. Wall time was 157.03 seconds. The reported maximum resident set size was 395,247,616 bytes.
- JSS build: `sh scripts/reproduce_jss_manuscript.sh NEW_OUTPUT` with TinyTeX-1 v2026.11, pdfTeX 1.40.29, BibTeX 0.99e and JSS class 3.6. Two output directories produced identical PDFs. The last LaTeX pass had no overfull boxes, unresolved citations or pending label changes.
- PDF review: all 11 pages were rendered and inspected for layout. Five figure images use the frozen inputs, all four tables use frozen CSV cells, and numeric tokens come from the original Phase 29 receipt. The PDF contains 10 clickable DOI destinations and 2 official archive links. See the [frozen bibliography audit](../BIBLIOGRAPHY_AUDIT.md) for publisher metadata limitations. The draft explicitly retains both false-certificate denominators.
- Workspace checks: 1,094 tests passed in 256.91 seconds in the existing workspace, which contains additional local test files. Ruff lint, Ruff format check, strict mypy, shell syntax and Git whitespace checks passed. The replay also checked the historical SHA-256 manifests.
- Clean public checkout: after `uv pip install --python "$p" --no-deps -e .`, `"$p" -m pytest` passed all 829 tracked tests in 139.95 seconds. This run installed the optional pytest-cov plugin into the test environment. Ruff lint, Ruff format, and strict mypy also passed in the public checkout.
- Wheel-only check: 803 passed and 26 failed in 34.69 seconds. The failures share a cause. Legacy simulator commands and the evidence builder locate experiment modules outside the installed wheel. The benchmark replay uses the public checkout and succeeded.

This record describes internal verification. No external researcher participated and no new benchmark configurations were evaluated.
