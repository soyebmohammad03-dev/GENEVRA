# GENEVRA research guide

GENEVRA has two connected lines of work. The simulator supports controlled digital-organism experiments. The measurement program studies when a paired score or calibration certificate is defensible. Synthetic uncertainty benchmarks provide known-truth stress tests. They do not establish that simulator scores measure biological fitness, evolvability, or adaptive forecasts.

## Start here

- [Capability and inventory](INVENTORY.md) maps the checked-in repository and archived research.
- [Experiment index](EXPERIMENT_INDEX.md) links the frozen phases, assumptions, and results.
- [Integrated methodology and contribution matrix](METHODOLOGY.md) explains what the studies establish.
- [Manuscript foundation](MANUSCRIPT_FOUNDATION.md) records the strongest candidate paper and qualification gates.
- [Notebook](../../notebooks/certification_evidence.ipynb) compares precision, coverage, certification and the identification floor from verified outputs.
- [Baseline simulator architecture](../architecture.md), [experiment interface](../experiments.md) and [committed evidence](../../research_evidence/README.md) document the original program.

## Reproduce

The archive is a technical GitHub prerelease asset. The [catalog](archive.json) pins its URL, size and SHA-256, with the original archive identities. The replay command verifies the archive and each payload, uses each study's source snapshot, and runs the independent checker. It writes only to a new output directory.

```sh
uv venv --python 3.12.15 .venv-replay
uv pip install --python .venv-replay/bin/python -r docs/research/requirements-replay.txt
.venv-replay/bin/python scripts/replay_research.py --output /tmp/genevra-replay
```

Use `--archive /path/to/GENEVRA_PHASE20_REPLAY.zip` for an offline copy or repeat `--phase 18 --phase 19` for selected phases. The verifier still extracts and checks the whole archive. The audit-only Phase 17 and 19 jobs read verified archived data instead of acquiring observations. The coverage-envelope extension replays its saved sufficient counts. Earlier full bundles remain immutable. The public capsule omits local execution logs, duplicate nested archives, and older rendered media. Its replayed numeric outputs and frozen input files are byte-preserved. Cross-platform formatting and numerical libraries can change bytes. The verified reference platform is macOS arm64.

For the original simulator and repository tests:

```sh
uv venv .venv
uv pip install --python .venv/bin/python -e '.[dev,viz]'
.venv/bin/pytest -q --cov
.venv/bin/ruff check .
.venv/bin/ruff format --check .
.venv/bin/mypy
.venv/bin/genevra verify-evidence research_evidence
```

Follow the [notebook instructions](../../notebooks/README.md) for kernel execution and figure provenance. Report the commit, archive digest, versions, exact command, and discrepancies when reproducing. Cite [CITATION.cff](../../CITATION.cff) and the exact phase/protocol. The existing [MIT license](../../LICENSE) applies to GENEVRA code. Literature and external resources retain their own rights. The replay capsule contains GENEVRA-generated synthetic and simulator observations, without third-party datasets or personally identifying measurements.
