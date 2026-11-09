# Reproduce or enter the allocation challenge

Reference environment is macOS arm64, CPython 3.12.15 and the pinned Phase 23 replay environment. The frozen acquisition protocol reads the immutable Phase 19 configuration and checks its digest. The Phase 25 protocol and design are also pinned. Each command creates a new output directory.

```sh
git clone --branch research/publication-development https://github.com/soyebmohammad03-dev/GENEVRA.git
cd GENEVRA
scratch=$(mktemp -d)
uv venv --python 3.12.15 "$scratch/venv"
py="$scratch/venv/bin/python"
uv pip install --python "$py" -r docs/research/phase_23/requirements-macos-arm64.txt
d=docs/research/phase_25
(cd "$d" && shasum -a 256 -c SHA256SUMS)
PYTHONPATH=src "$py" experiments/allocation_challenge.py --output "$scratch/comparison"
"$py" scripts/verify_allocation_challenge.py "$scratch/comparison"
for f in results.json contrasts.csv allocation.svg receipt.json; do
  cmp "$d/$f" "$scratch/comparison/$f"
done
```

The runner writes all 36,864 method-replicate rows to `raw.csv` (about 5 MiB), 144 summary cells, 18 contrasts, PNG and SVG, and a receipt. Raw counts, allocations, pilot outcomes, costs, realized interval endpoints and decision flags are preserved. The published receipt pins the raw CSV and both figures. It records the NumPy and Python versions. Byte-exact figure checks depend on the reference environment and fonts. Report cross-platform numeric and rendering discrepancies separately.

The separate verifier reads the saved raw rows, uses no GENEVRA imports, and checks cost, shared pilot, nested counts, all classifications, summaries and paired contrasts. It independently enumerates the variance optimum on the first replicate of each cell and reconstructs the first interval for every method and cell using log-likelihood inversion and closed-form envelope endpoints. Counts and categories are exact. Floating checks use absolute 1e−9 for summation and inversion roundoff. Deterministic replay checks the full raw output against the receipt. The archived [Phase 24 replay](../phase_24/REPRODUCE.md) is the historical integrity check.

## Submit a competing allocation

Supply a trusted Python file defining `allocate(request)` and returning a tuple of two positive Python integer independent-unit counts. The [example](example_policy.py) implements proportional allocation. The request exposes `budget` (inference budget after the pilot), `costs` (including duplicate-block row charges), `weights`, `minimum`, `pilot_hits`, and `pilot_n`. The integer counts must exactly spend the remaining budget. The scorer owns inference, scenario truths and evaluation. It rejects invalid counts and writes a separate run. No frozen artifact is overwritten.

```sh
PYTHONPATH=src "$py" experiments/allocation_challenge.py --output "$scratch/entrant" \
  --entrant "$d/example_policy.py"
"$py" scripts/verify_allocation_challenge.py "$scratch/entrant"
```

Return the source and digest, environment, receipt, `results.json` and any failure logs. Declare all tuning and information used. The loader runs local Python code and is no sandbox. Public scenario laws, code and seeds are accessible, so a scorer cannot guarantee blinding or certify a submission's access. Entrant comparisons are descriptive. The prospective holdout protocol is separate. No actual external submissions have been received.
