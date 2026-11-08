# External reproduction

## Verified environment and inputs

The Phase 23 run used CPython 3.12.15, macOS 27.0.1 build 26A434, arm64, and uv 0.12.23. [Replay dependencies](requirements-macos-arm64.txt) pin all 49 packages used by the archive, notebook and Census reconstruction. [Quality dependencies](requirements-quality-macos-arm64.txt) include the clean checkout checks. Work from a fresh research-branch checkout and a scratch output directory. The internal clean verification used an export of the public parent tree at `30df2cd9337b888d85f51d7150c2a4f59a6b618d`. Phase 23 adds documents and environment specifications. For a like-for-like preexisting test inventory use that parent tree.

The public [archive catalog](../archive.json) specifies the immutable prerelease asset, size, original bundle hashes and outer SHA-256 `bf0f1e979c92cf2228ed52b58021c4ffcc1be48dd9cf49e83a57d214a56afd91`. Archive members include frozen sources, seeds, raw or sufficient observations, derived tables and independent computational checkers. It excludes redundant local archives, some logs and older media. No private developer environment or restricted field data is needed.

```sh
git clone --branch research/publication-development https://github.com/soyebmohammad03-dev/GENEVRA.git
cd GENEVRA
d="$PWD/docs/research/phase_23"
out=$(mktemp -d)
(cd "$d" && shasum -a 256 -c SHA256SUMS)
uv venv --python 3.12.15 "$out/venv"
py="$out/venv/bin/python"
uv pip install --python "$py" -r "$d/requirements-macos-arm64.txt"
"$py" scripts/replay_research.py --output "$out/replay"
```

The output must contain ten checked entries, `phase-11` through `phase-19` plus `phase-19-extension`, and `receipt.json`. The program fails on an outer or payload checksum discrepancy. Phase 17 and Phase 19 audits read archived observations and the extension replays sufficient counts. Early replay jobs execute frozen historical simulations and compare their outputs to archived results. None acquires field observations. For offline replay use `--archive` with a copy matching the catalog. If GitHub download fails, diagnose access first and do not substitute an unpinned archive. Cross-platform numerical or rendering differences should be recorded with their versions, paths and magnitudes.

```sh
GENEVRA_REPLAY="$out/replay" GENEVRA_NOTEBOOK_FIGURES="$out" \
  "$py" - "$out" <<'PY'
import sys
from pathlib import Path
import nbformat
from nbclient import NotebookClient
out = Path(sys.argv[1])
book = nbformat.read("notebooks/certification_evidence.ipynb", as_version=4)
nbformat.validate(book)
nbformat.write(NotebookClient(book, timeout=60, kernel_name="python3").execute(),
               out / "executed.ipynb")
PY
cmp "$out/identification_floor.png" docs/research/identification_floor.png

ext=docs/model_repair/phase_19/extension
"$py" "$ext/plot.py" "$out/replay/phase-19-extension/results.json" "$out/coverage_envelope"
cmp "$out/coverage_envelope.svg" "$ext/coverage_envelope.svg"

curl -fLsS https://www2.census.gov/programs-surveys/popest/tables/2020/2020-demographic-analysis-estimates/Table-3_PES-sex.xlsx -o "$out/Table-3_PES-sex.xlsx"
curl -fLsS https://www.census.gov/newsroom/press-releases/2024/undercounts-overcounts-children-2020-census.html -o "$out/2024-release.html"
"$py" docs/research/phase_21/reconstruct.py "$out/Table-3_PES-sex.xlsx" "$out/2024-release.html" "$out/census.json" --figure "$out/census.png"
cmp "$out/census.json" docs/research/phase_21/census_diagnostic.json
cmp "$out/census.png" docs/research/phase_21/census_diagnostic.png

PYTHONPATH=src "$py" experiments/prospective_design_check.py "$out/design_receipt.json"
cmp "$out/design_receipt.json" docs/research/phase_22/design_receipt.json
```

If kernel selection fails, confirm that the kernel is in the pinned interpreter environment. The workbook is hash-checked. The live HTML may change in layout or surrounding copy, so the parser validates the national row and exact numerical reconstruction. If a source disappears or the selected vintage changes, report it before substituting anything. When figures differ across platforms, report numeric equality separately from pixel or byte equality.

## Independent numerical adjudication

Inspect the verified archive data and checkers to reconstruct Phase 18 coverage and certificate denominators and paired utility, then replay Phase 19 endpoint propagation and the equal-spend comparison. See the [experiment index](../EXPERIMENT_INDEX.md) for each study's frozen methods. Independently verify the fixed-span width calculation with the endpoints in the [manuscript foundation](MANUSCRIPT_FOUNDATION.md). For Census extract Table 3 cells C5:E5 with a second reader and recompute the 2024 percentage from the April release counts. For Phase 22 compute zero-event safety with `1 - .02**(1/12)`, and fixed-n power by summing the binomial lower tail at the greatest passing event count. These are checks of known-input calculations. Field provenance assumptions require their own evidence.

The [receipt](reproduction-receipt.json) records observed input and output digests.

## Quality commands

```sh
uv pip install --python "$py" -r "$d/requirements-quality-macos-arm64.txt"
uv pip install --python "$py" --no-deps -e '.[dev,viz]'
"$out/venv/bin/pytest" -q --cov
"$out/venv/bin/ruff" check .
"$out/venv/bin/ruff" format --check .
"$out/venv/bin/mypy"
"$out/venv/bin/genevra" verify-evidence research_evidence
```

Expect 748 passes in the public tree. The local workspace includes earlier uncommitted tests and passed 1,013.

Record the checked-out commit, interpreter and package versions, archive digest, commands and output paths, test counts, and any discrepancies. Keep the replay output and notebook separate from committed historical files. Return a reviewer conflict and independence statement with the reproduction record.
