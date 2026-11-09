# Reproduce Phase 22

The design receipt contains analytic power and deterministic **synthetic design fixtures**. It is not a dataset of field measurements. There is no stochastic campaign or RNG seed. From the repository root in the project environment:

```sh
d="$PWD/docs/research/phase_22"
out=$(mktemp -d)
(cd "$d" && shasum -a 256 -c SHA256SUMS)
.venv/bin/python experiments/prospective_design_check.py "$out/design_receipt.json"
cmp "$d/design_receipt.json" "$out/design_receipt.json"
.venv/bin/pytest -q tests/test_validation_design.py
```

The checker uses analytic calculations and small fixed populations to expose correct references, shared blindness, unsampled strata, valid and invalid off-frame bounds, nonresponse and unmatched costs. A narrow wrong bound may produce an apparently correct decision while excluding the known fixture truth. These examples test code and assumptions only. The exact reference inversion is implemented for known fixed SRSWOR counts and a supplied cap. It does not implement a field area audit, estimated cap confidence set, cluster adjustment or field-data ingest.

Independently reconstruct power by summing binomial probabilities, and hypergeometric confidence coverage by enumerating all feasible observed counts for each true total on a small roster. Verify why an unresolved label is retained and why a zero-draw stratum has full support. Audit separately the statement that a source cap is scientifically valid. Numerical verification here is local, even where a separate implementation checks it.

The [historical replay guide](../README.md) and [notebook](../../../notebooks/README.md) reproduce the archived synthetic findings and identification-floor figure. The [Phase 21 reviewer instructions](../phase_21/REPRODUCIBILITY.md) reproduce the separate Census diagnostic. A third-party review should return commands, hashes, discrepancies, independence disclosures and its assessment of whether the proposed access design can be realized.
