# Cross-platform numerical audit

## Controlled diagnostic

This investigation repeats the existing software example at seed 0. Each platform ran the native policy twice and a diagnostic-only stable sort twice. It kept the baseline genome, simulator, selection pressure, elite fraction, tournament and configuration fixed. The only intervention was passing `kind="stable"` to the elite ranking. Every selection records the ordered fitness scores, candidate elites, selected parents and hashes of the PCG64 state before and after selection. Results include the original serialized trajectory and lineage. The [macOS trace](traces/macos-arm64.json.gz), [Ubuntu trace](traces/ubuntu-x86_64.json.gz) and [comparison receipt](portability-receipt.json) preserve the intermediate values and NumPy build metadata.

- macOS 27.0.1 arm64, CPython 3.12.15, NumPy 2.5.4 with Accelerate, installed Phase 30 wheel.
- Ubuntu 24.04 x86-64, CPython 3.12.16, NumPy 2.5.4 with scipy-openblas, installed from repository source. [Ubuntu workflow and raw trace artifact](https://github.com/soyebmohammad03-dev/GENEVRA/actions/runs/42647027640)
- Both used `OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 PYTHONHASHSEED=0`. Accelerate need not honor OpenBLAS controls. The tested baseline processes lifetimes serially. No process-parallel experiment was introduced.

Run the following in the respective installed environment. Use a fresh filename per platform. The two runs per policy must return equal serialized result objects and selection rows within each invocation.

```sh
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 PYTHONHASHSEED=0 python scripts/diagnose_baseline_portability.py trace.json
python scripts/compare_baseline_portability.py mac.json ubuntu.json comparison.json
```

## Results and identification

The native final means reproduced Phase 30 at 63.75 and 75.25. Generation 0 already showed differences in continuous diversity and instantaneous novelty, while the decision traces agreed. At generation 1 (zero-based), fitness inputs and RNG states before and after selection agreed exactly. Three candidates included in the elite cutoff tied at 70. Native elite indices were [23, 0, 3] on macOS and [23, 0, 8] on Ubuntu. Tournament selections agreed at that step. The default NumPy sort has no stable tie guarantee. [NumPy argsort specification](https://numpy.org/doc/stable/reference/generated/numpy.argsort.html)

Under stable ordering, the two environments agreed on all 15 selection traces and all 384 lineage records, including genome hashes. Final means were 68.0 in both environments. This intervention establishes an equal-fitness elite tie as the first observed decision divergence and accounts for the observed lineage divergence in this controlled example. The diagnostic changes behavior on both platforms and is intentionally confined to the probe.

The largest residual trajectory difference under stable ordering was 2.384185791015625e-7 in genome centroid shift. Smaller residuals remain in genotypic diversity, behavioral diversity and both novelty summaries. Float32 controller and genome operations and NumPy reductions are possible routes. BLAS, architecture, NumPy build configuration, and Python patch version were confounded between environments. The exact low-level origin of the continuous residuals remains unidentified.

The first discrete divergence preceded any difference in the recorded selection RNG states or fitness inputs, and was visible in memory before JSON serialization. Repeating with fixed environment controls preserved the native difference. This supports an unstable tie rule as the decision mechanism in this example, without ruling out seed, numerical or runtime dependencies in other workloads. See the [reproducibility contract](REPRODUCIBILITY_CONTRACT.md).
