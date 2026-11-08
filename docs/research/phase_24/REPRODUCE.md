# Reproduce from a public checkout

Reference environment is macOS arm64, CPython 3.12.15 and uv. Allow 2 GB of free disk for the environment and extracted capsule. The pinned environment comes from the checked-in [Phase 23 replay requirements](../phase_23/requirements-macos-arm64.txt). For alternate platforms, report any font, rendering or numeric differences separately. A byte mismatch fails the reference command. Inspect the preserved partial run rather than relaxing a check.

```sh
git clone --branch research/publication-development https://github.com/soyebmohammad03-dev/GENEVRA.git
cd GENEVRA
git rev-parse HEAD
(cd docs/research/phase_24 && shasum -a 256 -c SHA256SUMS)
scratch=$(mktemp -d)
uv venv --python 3.12.15 "$scratch/venv"
py="$scratch/venv/bin/python"
uv pip install --python "$py" -r docs/research/phase_23/requirements-macos-arm64.txt
"$py" scripts/benchmark_challenge.py reproduce --output "$scratch/replay"
```

The runner verifies the catalog SHA-256 and every source/config/observation member before executing the ten frozen jobs. An offline copy of the pinned asset can be passed with `--archive`. The jobs analyze existing frozen observations. Some also reexecute historical generators within their original replay boundary. See the archived per-phase scripts for generating the original synthetic data into new locations if needed. Do not rerun acquisition to score an entry. The Phase 18 raw checker reconstructs the baseline intervals and flags. The Phase 19 extension checker reconstructs likelihood intervals and envelope calculations from counts. The Phase 24 scorer re-derives target and anchor error from raw source counts and aggregates verified replicate decisions. It reads the final CSVs only to compare reproduced metrics. The scorer does not re-estimate interval endpoints. The published-table checks and the separate raw checkers run first.

The output includes an executed notebook, regenerated Phase 18 matched-access figure, Phase 19 coverage-envelope figure, identification-floor figure and a `challenge-verification.json` report with exact counts, tolerance, inputs, environment, contrasts and figure digests. Phase 21's [Census diagnostic](../phase_21/REPRODUCIBILITY.md) is a separate external descriptive artifact. Check counts and key inventories exactly and numeric differences with absolute tolerance 1e−9, zero relative tolerance. This tolerates inversion and summation roundoff while remaining far below one count divided by the largest relevant denominator. No tolerance changes classification boundaries. Phase 18's archived separate checker also verifies admission, source hashes and simultaneous exact safety intervals.

## Competing implementation

```sh
asset="$scratch/replay/GENEVRA_PHASE20_REPLAY.zip"
"$py" scripts/benchmark_challenge.py prepare --archive "$asset" --output "$scratch/prepared"
# Run your own policy on prepared/acquisition-package.json and write your submission CSV.
"$py" scripts/benchmark_challenge.py score --archive "$asset" --output "$scratch/scored" \
  --submission /absolute/path/to/submission.csv
```

The scorer verifies the same capsule. It uses the archived baseline decisions for the paired reference. The full reproduction workflow separately verifies those decisions from frozen counts. Each action requires a fresh output directory and never overwrites historical artifacts. The `submission-score.json` output records the submission hash and exploratory comparison. Provide exact commit, commands, hashes and discrepancies with any reproduction report.

For quality checks, install the [quality pins](../phase_23/requirements-quality-macos-arm64.txt), then use `uv pip install --python "$py" --no-deps -e '.[dev,viz]'`. Run pytest with `-q --cov`, Ruff check and format check, strict mypy, and `genevra verify-evidence research_evidence` from that environment.
