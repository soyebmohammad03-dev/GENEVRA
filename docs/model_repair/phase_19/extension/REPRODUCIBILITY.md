# Reproduce the extension

From the repository root. The NumPy pin matches the frozen receipt. Use Python 3.12.15.

```sh
uv venv --python 3.12.15 .phase19-venv
uv pip install --python .phase19-venv/bin/python numpy==2.5.4
d=docs/model_repair/phase_19/extension
(cd "$d" && shasum -a 256 -c SHA256SUMS)
export PYTHONPATH=src OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1
out=$(mktemp -d)
.phase19-venv/bin/python experiments/coverage_envelope_study.py acquire "$d" "$out/raw.json" "$out/results.json"
.phase19-venv/bin/python "$d/verify.py" "$d/config.json" "$out/raw.json" "$out/results.json"
cmp "$d/results.json" "$out/results.json"
(cd "$out" && shasum -a 256 -c "$OLDPWD/$d/GENERATED_SHA256SUMS")
```

On a platform with different rounding, rely on the independent verifier and decision counts rather than expecting byte equality. The raw JSON contains scenario-level sufficient binomial counts, independent denominators, duplicate multipliers, seeds, frozen hashes and runner/module hashes. No full sample rows were generated. Production mode analyze verifies raw identity without overwriting it. Use a new output path for replay. The local reproducibility ZIP includes raw data and results. The public branch includes the frozen recipe, verified derived results, figure and generated-data checksums. It does not require unpublished experiments or private data.

Repository validation uses pytest, Ruff, strict mypy and the evidence verifier already declared in the project. The new analysis requires no additional runtime dependency. Figure generation uses the existing visualization extra with Matplotlib 3.11.2. See the bundle command record for the actual environment and resource logs.
