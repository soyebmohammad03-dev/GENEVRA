# Installation and quick start

Install Python 3.11 or 3.12 and [uv](https://docs.astral.sh/uv/getting-started/installation/). Start from a fresh clone of the research branch. Keep the build outputs and the installed environment outside the checkout.

```sh
git clone --branch research/publication-development --single-branch https://github.com/soyebmohammad03-dev/GENEVRA.git
cd GENEVRA
checkout=$PWD
out=$(mktemp -d)
uv build --out-dir "$out/dist"
uv venv --python 3.12 "$out/venv"
p="$out/venv/bin/python"
g="$out/venv/bin/genevra"
wheel="$out/dist/genevra-0.1.0-py3-none-any.whl"
uv pip install --python "$p" "$wheel"
uv pip check --python "$p"
mkdir "$out/example"
cd "$out/example"
"$g" --help
"$g" run --seed 0 --output 'baseline result.json'
"$g" inspect 'baseline result.json'
"$g" analyze 'baseline result.json'
"$g" verify-evidence "$checkout/research_evidence" --output evidence.json
```

The basic example writes a seeded JSON trajectory with 15 completed generations and 24 final organisms in the tested configuration. The analysis reports stagnation and separate fitness information. Evidence verification checks the supplied evidence directory and reports checksum, manifest and seed-split issues. Read the historical [evidence guide](../../research_evidence.md) for scope and interpretation.

The package has one mandatory dependency, NumPy 1.26 or later. Install optional visualization support into the same environment before using figure, full artifact or evidence-generation commands. For example, install `"$wheel[viz]"` in place of `"$wheel"` in the command above. For editable development, install `".[dev,viz]"` with `uv pip install --python "$p" -e ".[dev,viz]"` from the checkout. The source distribution also supports non-editable installation.

Remove GENEVRA when finished. This removes its CLI and import while retaining the environment and generated outputs.

```sh
uv pip uninstall --python "$p" genevra
```

## Command and configuration reference

Run `genevra SUBCOMMAND --help` for positional arguments, defaults and flags. The distribution gate checks the main help and every subcommand and writes text help files. The installed commands fall into these groups.

| Task | Commands and inputs |
|---|---|
| Simulate and inspect | `run` uses a fixed baseline configuration and accepts a seed and an optional JSON output. `inspect` and `analyze` read a stored JSON trajectory. |
| Explore and compare | `discover`, `hypothesis`, `replicate`, `literature`, `reproduce`, `falsify` and `boundary-search` use stored results or registered built-in cases. `compare` lists separate checkout scripts. |
| Run or resume campaigns | `campaign`, `campaign-status`, `campaign-resume`, `literature-campaign` and `replication` accept the seeds, registered cases and output paths detailed in their help. |
| Analyze mechanisms and populations | `open-endedness`, `innovation`, `activity`, `robustness`, `generalization`, `analyze-mechanisms`, `ecology`, `coevolution`, `niches`, `interactions`, `population-analysis`, `predict-evolution` and `perturbation` expose task-specific controls. |
| Create and verify outputs | `figures`, `tables`, `artifacts`, `report`, `reproduce-evidence` and `verify-evidence`. Plotting and the complete evidence builder require the visualization extra. Give evidence generation a fresh output directory. |

For programmatic configuration, see the [architecture](../../architecture.md), [experiment definitions](../../experiments.md) and [reproducibility notes](../../reproducibility.md). Model, evolution and experiment settings are typed configuration objects. The archived studies have separate frozen settings, seed policies and receipts. A baseline run is a software example.

## Publication benchmark

The publication benchmark uses the checkout, pinned macOS arm64 environment and separately verified raw archive. Follow the existing [publication reproduction guide](../../research/phase_29/jss/SOFTWARE_GUIDE.md) for the registered replay and JSS typesetting. The wheel contains the three runtime scripts needed by the installed simulator and evidence builder. Publication scripts, study protocols, data and rendered figures stay in the checkout or archived supplement.

The distribution gate is `sh scripts/check_distribution.sh 3.12 NEW_OUTPUT`. It builds both formats, uses environments and a working directory outside the source checkout, verifies outputs, runs the tracked tests and checks removal.

## Troubleshooting and citation

- If `genevra` is missing from `PATH`, call the executable directly in the environment's `bin` directory as above.
- If a runtime script is missing, rebuild and reinstall from the verified revision. The audit checks the three wheel copies against the checkout.
- If plotting reports a missing dependency, install the visualization extra. Headless validation uses `MPLBACKEND=Agg`.
- Use quoted paths and writable output directories. A checksum mismatch requires checking the exact revision or the archive against its manifest before using the result.
- Use the [citation record](../../../CITATION.cff) and include the exact Git commit and frozen study protocol. See the [project license](../../../LICENSE) and [redistribution audit](LICENSE_AND_REDISTRIBUTION_AUDIT.md).
