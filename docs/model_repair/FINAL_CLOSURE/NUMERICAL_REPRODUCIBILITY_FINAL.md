# Final numerical reproducibility assessment

Phase 31 isolated the discrete divergence to a native elite tie. This follow-up isolates the remaining continuous differences in the same seed-zero software example. Both runs used the existing baseline with the diagnostic stable tie policy, one configured OpenBLAS thread, one OMP thread, and `PYTHONHASHSEED=0`. macOS 27.0.1 arm64 used Python 3.12.15 and NumPy 2.5.4 linked to Accelerate. Ubuntu 24.04 x86-64 used Python 3.12.16 and NumPy 2.5.4 linked to scipy-openblas. See the [Phase 31 baseline contract](../phase_31/REPRODUCIBILITY_CONTRACT.md).

The probe recorded shape, SHA-256 of little-endian float32 bytes, native norm and explicit reference norm for each one-dimensional vector entering `numpy.linalg.norm` during metric snapshots. The intervention returns the float32 cast of the square root of a high-precision sum of squares of the same float32 inputs. It changes only diagnostic metric evaluation. The installed implementation for these operands takes the square root of the float32 dot product. [NumPy norm documentation](https://numpy.org/doc/stable/reference/generated/numpy.linalg.norm.html)

| Check | Observed result |
|---|---|
| Ordered metric norm operands | All 66,124 matched by exact bytes and shape. There were 61,970 length-10 operands and 4,154 length-254 operands. |
| Native norm outputs | 12,009 differed. Maximum absolute difference was 7.62939453125e-6. The first norm was 38.06574249267578 on macOS and 38.065738677978516 on Ubuntu. |
| Explicit reference outputs | All 66,124 were exactly equal. |
| Stable ties with explicit norms | All 15 recorded trajectories by generation, all 15 selection rows and all 384 lineage records matched exactly. |

The intervention accounts for the Phase 31 residuals in this probe. The difference is observable before serialization, after both platforms have received identical operands. The native norm path is the immediate source of the variation. Differences in dot-product reduction, backend kernels and floating-point implementation are plausible contributors. The design does not attribute the discrepancy to a particular instruction, kernel, or reduction tree. The synthetic publication benchmark is a separate workflow. There is no demonstrated scientific decision impact from these metric differences in the tested probe and no established equivalence margin for other analyses.

```sh
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 PYTHONHASHSEED=0 python scripts/diagnose_metric_reductions.py trace.json
python scripts/summarize_metric_reductions.py mac.json ubuntu.json receipt.json
```

The [receipt](metric-reduction-receipt.json) records the operand widths, observed outputs and SHA-256 for both full traces. Obtain the Ubuntu trace from the [GitHub diagnostic run](https://github.com/soyebmohammad03-dev/GENEVRA/actions/runs/42651323963) while retained, or rerun the tracked workflow. Regenerate a macOS trace using the pinned environment above.

**Contract.** Production native trajectories may differ across platforms when ties choose different elites. The stable-policy and explicit-norm result applies to this diagnostic only. Use the pinned macOS replay environment and exact artifact checksums for publication claims. Interpret native continuous summaries across environments in light of rounding, and justify analysis-specific tolerance independently when needed. The production algorithm and frozen artifacts retain their original bytes.
