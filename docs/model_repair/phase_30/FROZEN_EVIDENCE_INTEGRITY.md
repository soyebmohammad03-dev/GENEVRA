# Frozen evidence integrity

Baseline `e3b2edc1a7eb429be28af3969ad2c92264c0bd93` is the public JSS preparation revision. Development used a separate clean worktree because the primary checkout contains local historical material and in-progress edits. The implementation diff was checked against the baseline. No files changed in `configs/`, `experiments/`, `results/`, `research_evidence/`, `docs/research/`, or the tracked Phase 19 model-repair evidence.

```sh
git diff --exit-code e3b2edc1a7eb429be28af3969ad2c92264c0bd93 -- configs experiments results research_evidence docs/research docs/model_repair/phase_19
shasum -a 256 -c docs/research/phase_29/FROZEN_SHA256SUMS
(cd docs/research/phase_28 && shasum -a 256 -c SHA256SUMS)
(cd docs/research/phase_29 && shasum -a 256 -c SHA256SUMS)
(cd docs/research/phase_29/jss && shasum -a 256 -c SHA256SUMS)
```

The tracked manifests cover experiment configurations, registered results and statistical summaries, figure and table data, manuscript text, and reproduction receipts. The standalone CLI also verified the curated evidence checksums and links. The original [raw replay capsule record](../../research/archive.json) specifies SHA-256 `bf0f1e979c92cf2228ed52b58021c4ffcc1be48dd9cf49e83a57d214a56afd91`. The separately downloaded capsule matched that digest, and all 1,513 payload members matched the internal manifest. The publication-only path `sh scripts/reproduce_final_research.sh --publication-only NEW_OUTPUT` regenerated the original review PDF and receipt byte for byte using existing results. Software test fixtures and the basic example write to fresh output directories. No full benchmark campaign was run for Phase 30.
