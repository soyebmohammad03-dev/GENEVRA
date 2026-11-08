# Installing and reproducing GENEVRA

The verified target is macOS arm64 with CPython 3.12.15. Start with Git, [uv](https://docs.astral.sh/uv/getting-started/installation/), an Internet connection, and a writable output volume. The JSS PDF also requires TeX Live with pdfLaTeX, BibTeX, Latin Modern and the dependencies used by the official JSS class. The recorded build used TinyTeX-1 v2026.11. Commands below run from the repository root after cloning. Each build takes a fresh output path.

```sh
git clone --branch research/publication-development --single-branch \
  https://github.com/soyebmohammad03-dev/GENEVRA.git
cd GENEVRA
out=$(mktemp -d)
uv venv --python 3.12.15 "$out/install"
p="$out/install/bin/python"
uv pip install --python "$p" -r docs/research/phase_23/requirements-macos-arm64.txt
uv pip install --python "$p" --no-deps .
uv pip check --python "$p"
"$out/install/bin/genevra" --help
"$out/install/bin/genevra" verify-evidence research_evidence
"$p" -m pydoc genevra.analysis.coverage_envelope
"$p" scripts/benchmark_reference.py --help
```

The lock lists NumPy, plotting and notebook dependencies, and pytest. Installing the project from source also resolves its declared Hatchling build dependency. The installed command covers the general GENEVRA simulator. The standalone publication scripts below additionally require the checked-out research inputs.

## Worked example

```sh
(cd docs/research/phase_29/jss && shasum -a 256 -c SHA256SUMS)
sh scripts/reproduce_final_research.sh --publication-only "$out/review"
PYTHON="$p" sh scripts/reproduce_jss_manuscript.sh "$out/jss"
cmp docs/research/phase_29/jss/manuscript.pdf "$out/jss/manuscript.pdf"
```

The first build checks and renders existing evidence. Its `final/` directory contains the original technical review manuscript and audit receipt. The JSS build stages LaTeX, BibTeX, figures, a compiled bibliography and the candidate PDF. It verifies the official template archive before compilation. Set `JSS_TEMPLATE_ZIP` to an absolute path to the verified ZIP to use an offline copy. Byte comparison of the JSS PDF is verified for the recorded TeX setup.

For the complete frozen replay, including numerical verification, use the following command. The runner verifies the archive against the recorded digest and file manifest before replay. It also accepts the path to a previously downloaded verified archive as a second argument.

```sh
sh scripts/reproduce_final_research.sh "$out/replay"
```

Compare `$out/replay/final/audit-receipt.json` with the [tracked receipt](../rendered/audit-receipt.json). For the registered matched-cost comparison, covered-and-precise counts are 1/256 for the width proxy, 104/256 for paid-pilot Neyman, and 229/256 for equal spend. The shared-blind-spot diagnostic records 180 false certificates across 512 runs and 180 false certificates among 180 issued. The one-sided upper bound of 40.73% applies to false certificates per run. The replay compares the frozen results and the original Phase 29 PDF byte for byte. It uses the original benchmark configuration and seeds.

## Software architecture and interfaces

| Layer | Role and interfaces |
|---|---|
| `src/genevra/` | Installed simulator, configuration and analysis modules. Use `genevra SUBCOMMAND --help` for arguments and `python -m pydoc genevra.analysis.coverage_envelope` for the interval API. |
| `experiments/allocation_challenge.py` | Frozen synthetic allocation drivers and registered conditions. The publication runner selects the archived protocol and verifies raw results. |
| `scripts/replay_research.py` | Archive validation and historical replay. Use the shell driver above for the supported end-to-end workflow. |
| `scripts/benchmark_reference.py` | Separate numerical implementation. `bernoulli_limits(k,n,alpha)` inverts the one-stratum fixed-look bound, `allocation_interval(...)` combines stratum limits, and `envelope(lo,hi,cap,hidden_cap)` expands for bounded undercoverage. `classify(...)` scores the frozen decision against synthetic truth. `binomial_upper(k,n,alpha)` computes a one-sided upper binomial limit. Its CLI requires the raw Phase 25 counts and Phase 18 replay inputs and writes a verification JSON report. |
| `scripts/build_publication.py`, `scripts/final_research_audit.py` | Reconstruct figures, tables, principal widths, and the technical review manuscript using verified inputs. |
| `scripts/build_jss_manuscript.py`, `scripts/reproduce_jss_manuscript.sh` | Transcribe the frozen manuscript into JSS LaTeX, preserve the citation and asset inventory, compile, and check references and layout warnings. |

For the historical package details see the [supplement](../SUPPLEMENT.md). For units, denominator distinctions, and assumptions see the [statistical review](../STATISTICAL_REVIEW.md). The separate reference implementation shares synthetic evidence inputs with the primary analysis. Its numerical check provides internal corroboration.

## Troubleshooting and license

- A digest mismatch means the build stopped before accepting changed inputs. Check the commit and archive URL against the archive record. Keep the failing inputs for inspection.
- An existing output path triggers refusal to overwrite the build. Choose a fresh directory and keep the earlier logs.
- Missing Python wheels or differing outputs on another platform require an environment and dependency review. Use the verified macOS arm64 configuration for exact comparison.
- If pdfLaTeX or BibTeX cannot be found, put the TeX Live binary directory on `PATH`. For missing fonts or LaTeX packages, install the dependencies used by the pinned JSS template and check the build log.
- If a fresh official template fails the SHA-256 check, use the pinned archive or audit the new template before updating the documented digest.

GENEVRA code is released under the repository [MIT license](../../../../LICENSE). The JSS template carries its own GPL terms. A submission-wide rights and license inventory remains open.
