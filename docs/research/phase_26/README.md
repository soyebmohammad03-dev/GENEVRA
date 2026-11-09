# GENEVRA Phase 26 scientific audit

Start with the [failure attribution](FINDINGS.md) and [completion report](PHASE_26_COMPLETION_REPORT.md). The negative primary allocation result remains part of the benchmark.

| Artifact role | Repository entry |
|---|---|
| Core research contribution | Frozen known-truth certification and allocation failures, documented in the [experiment index](../EXPERIMENT_INDEX.md) and [Phase 25 benchmark](../phase_25/README.md) |
| Supporting methodology | [Assumptions](ASSUMPTIONS.md), coverage envelope, concentration intervals and paired comparisons |
| Benchmark infrastructure | [Public reproduction challenge](../phase_24/README.md), source and data hashes, raw count checkers, entrant interface |
| Established comparator | Operational variance-aware, minimax, proportional, equal spend, direct and conservative refusal policies |
| Unsuccessful approach retained | GENEVRA width-proxy allocation as an audited negative comparator |
| Exploratory evidence | [Separate frozen sweep](PROTOCOL.md) and [machine-readable results](sensitivity.json) |
| Future research | [Independent review checklist](REVIEW_CHECKLIST.md), withheld synthetic evaluation and prospective empirical reference design |

The [revised manuscript foundation](MANUSCRIPT.md) and [publication positioning](POSITIONING.md) distinguish the benchmark from its established mathematical components. Earlier protocols and artifacts remain at their frozen paths.

## Reproduce

From a fresh research-branch checkout on macOS arm64:

```sh
git clone --branch research/publication-development https://github.com/soyebmohammad03-dev/GENEVRA.git
cd GENEVRA
scratch=$(mktemp -d)
uv venv --python 3.12.15 "$scratch/venv"
py="$scratch/venv/bin/python"
uv pip install --python "$py" -r docs/research/phase_23/requirements-macos-arm64.txt
d=docs/research/phase_26
(cd "$d" && shasum -a 256 -c SHA256SUMS)
PYTHONPATH=src "$py" experiments/allocation_challenge.py --output "$scratch/phase25"
PYTHONPATH=src:. "$py" experiments/allocation_audit.py "$scratch/phase25" "$scratch/phase26"
cmp "$d/reconstruction.json" "$scratch/phase26/reconstruction.json"
cmp "$d/sensitivity.json" "$scratch/phase26/sensitivity.json"
```

The reconstruction requires the exact published Phase 25 receipt and validates the underlying files before computing the audit. The reference platform pins all receipt bytes, including rendered figures. The verifier independently recomputes interval endpoints, counts and allocation objectives, while regeneration shares the NumPy RNG protocol and frozen design. Absolute endpoint tolerance is 1e−9. Treat alternate platform discrepancies as unresolved until verified, without replacing frozen outputs. The sensitivity sweep uses the production interval scorer and is verified by reproducibility and invariants, rather than a separate end-to-end statistical implementation. A fresh internal run is not external reproduction.
