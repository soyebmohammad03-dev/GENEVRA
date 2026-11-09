# Reproducibility contract

| Claim | Acceptance rule | Phase 31 result |
|---|---|---|
| Frozen artifact identity | Expected SHA-256 for the archive and all members. Byte-identical output and receipt under the documented macOS arm64 replay and TeX environment. | Verified internally. |
| Same-environment baseline replay | Fixed commit, seed, Python/NumPy build and runtime settings. Exact equality of JSON result objects and the 15 selection rows in two executions per policy. | Passed in both recorded environments. |
| Cross-platform native baseline identity | Equal generation-wise ordered fitness, selected parent IDs, RNG states and lineage. | Failed at the native elite tie. No promise of native cross-platform trajectory identity. |
| Cross-platform discrete diagnosis with stable ties | Equal fitness inputs, parent indices and RNG hashes at every generation, and equal lineage records. Treat changed counts or labels as failures. | Passed for the single stable-sort probe. |
| Cross-platform continuous output | Require matching structure, finite values and exact discrete fields. Report absolute discrepancies by named measure. A scientific equivalence margin would need independent justification for each use and a broader validation design. | Residuals reported. General numerical equivalence remains unestablished. |

The comparator enforces the expected first native decision divergence and the stable-policy decision and lineage checks. Regression tests confirm that finite numeric discrepancies are retained, while changed discrete values, missing fields and non-finite values are rejected. It applies no arbitrary rounding and supplies no acceptance threshold derived from the observed residuals. The diagnostic creates new software test output only. The registered benchmark, native tie rule and published claims remain frozen.
