# GENEVRA Phase 27 reproduction challenge

**Question.** Does a separately implemented reference recover the benchmark's key failures, and does the benchmark add a distinct test to existing sampling and reliability tools?

- [Mathematical design and comparators](DESIGN_AND_COMPARATORS.md)
- [Closest work, data and software matrix](NOVELTY.md)
- [External evaluation protocol](EXTERNAL_PROTOCOL.md)
- [Revised manuscript](MANUSCRIPT.md)
- [Machine-readable verification](reference-verification.json)
- [Completion report](PHASE_27_COMPLETION_REPORT.md)

The contribution is a frozen benchmark paired with a separate verification pathway. The unsuccessful allocation rule remains an important comparator. The challenge was executed internally and is open to independent scrutiny.

## Reproduce from a fresh checkout

Use macOS arm64, uv and sufficient room for the extracted capsule and virtual environment (allow 2 GiB).

```sh
git clone --branch research/publication-development https://github.com/soyebmohammad03-dev/GENEVRA.git
cd GENEVRA
(cd docs/research/phase_27 && shasum -a 256 -c SHA256SUMS)
scratch=$(mktemp -d)
sh scripts/reproduce_reference.sh "$scratch/reference"
```

The script requires a new output path. An optional second argument points to a capsule matching the [archive catalog](../archive.json) for offline use. The pinned dependencies still need to be available through uv. The script checks archive/member hashes, executes the ten historical replays, regenerates three principal figures, reexecutes Phase 25, compares its tables and figure, and produces a byte-compared Phase 27 JSON report. The raw CSV remains in the output directory with a published SHA-256. Time and environment should be reported separately. Do not substitute changed inputs or suppress a discrepancy.

The [reference implementation](../../../scripts/benchmark_reference.py) computes Phase 25 using standard-library likelihood inversion, analytic extreme-count cases, a closed-form hull and a discrete convex search. It scores every interval and checks exact budgets, published metrics, and paired contrast families. Phase 18 uses NumPy solely to decode the verified endpoint and certificate arrays. It recomputes truth, anchor error, coverage, labels, certification errors, utility contrasts and the simultaneous exact risk upper bounds. The historical checker independently reconstructs the Phase 18 arrays upstream. The new reference does not claim a second endpoint reconstruction for that phase. It imports no original estimators or verifiers. The specification, configuration, data, Python floating arithmetic and archive regeneration are shared.

Counts, decisions and integer costs must agree. Floating comparisons use absolute 1e−9 to accommodate inversion and arithmetic order. Cutoffs are applied before comparison without tolerance. The published output and figures use the pinned reference platform. For another platform report rendering and numeric discrepancies separately. The [external protocol](EXTERNAL_PROTOCOL.md) explains the scientific judgments a successful replay cannot supply.
