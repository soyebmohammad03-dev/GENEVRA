# External reproduction guide

The challenge is available for a researcher outside the project. The successful runs recorded here were internal. Begin with Git, uv, curl, unzip, and a macOS arm64 host. The exact software target uses CPython 3.12.15, NumPy 2.5.4 and the [pinned replay requirements](../../research/phase_23/requirements-macos-arm64.txt). Put TeX Live 2026 pdfLaTeX and BibTeX on PATH. The verified installation used TinyTeX-1 v2026.11 with pdfTeX 1.40.29 and BibTeX 0.99e.

```sh
git clone --single-branch --branch research/publication-development https://github.com/soyebmohammad03-dev/GENEVRA.git
cd GENEVRA
git rev-parse HEAD
(cd docs/model_repair/FINAL_CLOSURE && shasum -a 256 -c SHA256SUMS)
out=$(mktemp -d)
sh scripts/verify_publication_candidate.sh replay "$out/challenge"
(cd "$out/challenge" && shasum -a 256 -c SHA256SUMS)
```

The command downloads and verifies the [registered input archive](../../research/archive.json), verifies all its members, replays the frozen configurations, compares the original publication outputs, fetches the pinned official JSS style files and compiles the JSS PDF. It records environment, build logs and output hashes. The registered archive digest is `bf0f1e979c92cf2228ed52b58021c4ffcc1be48dd9cf49e83a57d214a56afd91`. A separate `render` invocation can check existing evidence without the full replay. To rerun the research driver using a local copy of the verified archive, pass the archive path as the second argument to `scripts/reproduce_final_research.sh`. For the TeX build, set `JSS_TEMPLATE_ZIP` to a verified local official ZIP if needed.

Check the [expected receipt](../../research/phase_29/rendered/audit-receipt.json) and [JSS manuscript](../../research/phase_29/jss/manuscript.pdf). The shared-blind results are 0/512 target intervals covered and 180 false certificates out of 512 runs, or 180/180 among issued. The simultaneous per-run upper bound is 40.73%. The allocation counts are 1/256, 104/256 and 229/256, with paired difference -40.23 points and interval [-57.21, -23.26]. A platform-dependent result in the baseline evolutionary example is separate from these frozen benchmark expectations.

For the candidate software, use CPython 3.12 to stage ASCII sources, then install from the resulting source directory or build the wheel.

```sh
uv run --no-project --python 3.12.15 python scripts/prepare_jss_source.py "$out/software"
cmp docs/model_repair/FINAL_CLOSURE/jss-software-inventory.json "$out/software/source-inventory.json"
(cd "$out/software" && uv build --out-dir "$out/distribution")
uv venv --python 3.12.15 "$out/installed"
uv pip install --python "$out/installed/bin/python" "$out/distribution/genevra-0.1.0-py3-none-any.whl"
"$out/installed/bin/python" -I scripts/build_jss_help.py "$out/software-help.html"
(cd "$out" && "$out/installed/bin/genevra" run --seed 0 --output example.json)
```

Keep the first failing log and use a fresh output path for retries. Record missing tools, platform changes and download deviations. If a digest differs, verify the source revision and official archive before using the result.

## Feedback and discrepancy template

Record reviewer identifier and relationship to the project, commit, OS, architecture, Python, NumPy and TeX versions, exact command, elapsed time, exit status, output hashes and whether each expected result matched. For a discrepancy, include the first mismatch, smallest reproducible command, expected and observed values or hashes, acquisition details, relevant log lines and whether a clean retry reproduced it. Share non-sensitive logs through the repository issue tracker or an agreed channel. Confirm attribution and permission to quote before the author records external reproduction.
