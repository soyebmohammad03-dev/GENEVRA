# GENEVRA publication and reviewer index

Use the **editorial LaTeX** as the source for conference formatting. Its compiled PDF is a JSS-style review candidate. Venue formatting, author declarations and attachment permissions remain pending. Cite the exact source revision and the frozen protocol.

## Current software and historical guidance

Use the [current installation and distribution guide](../model_repair/phase_30/INSTALLATION_VALIDATION.md) for a wheel or source install. The checksum-pinned [Phase 29 JSS software guide](../research/phase_29/jss/SOFTWARE_GUIDE.md) records an older wheel failure when commands loaded legacy experiments. That limitation is historical. The current wheel packages those experiment resources. Use the [final closure guide](../model_repair/FINAL_CLOSURE/EXTERNAL_REPRODUCTION_GUIDE.md) for frozen research reproduction and the version instructions below for manuscript selection.

## Manuscript versions

The exact pinned source checkout for all three builds below is
`9c1ff41d264dccf958dad4dd872b0a1f2f544395`. It contains the frozen PDFs, the editorial source and all three build routes. Current `main` carries those same inputs and the separate software handoff.

| Version | PDF and intended use | Source and references | PDF SHA-256 |
|---|---|---|---|
| Historical technical review | [Tracked technical PDF](../research/phase_29/rendered/GENEVRA-manuscript.pdf). Historical reference and release artifact. | [Markdown manuscript](../research/phase_29/MANUSCRIPT.md), [reference list](../research/phase_29/REFERENCES.md). This version is rendered by the technical build. | `5c3d07db5d10ffe949005d9a96f2f046d09a1fae905bb5e4e1b1348680f17a96` |
| Frozen JSS | [Tracked JSS PDF](../research/phase_29/jss/manuscript.pdf). Historical reproducibility target. | [Frozen LaTeX](../research/phase_29/jss/manuscript.tex), [BibTeX](../research/phase_29/jss/references.bib). | `3e3fe2b77828db2e1b59d240147b3ca58207adcea2f4be78c87e61bbeff58836` |
| Current editorial | `editorial/manuscript.pdf` in the local output directory. Generated review PDF for the conference adaptation. | [Editorial LaTeX](../model_repair/FINAL_CLOSURE/EDITORIAL_AUDIT/manuscript.tex), [same BibTeX](../research/phase_29/jss/references.bib), [editorial audit](../model_repair/FINAL_CLOSURE/EDITORIAL_AUDIT/EDITORIAL_AUDIT_REPORT.md). | `dd8747c8964c6e7bbbabadbb6ec51a33faa31bcd486f56bd1eeecaecc4e0ffa5` |

All three use the [five frozen figures](../research/phase_28/rendered/figures) and [four frozen table inputs](../research/phase_28/rendered/tables). The [index manifest](SHA256SUMS) records the tracked PDF, source, bibliography, figure, table and evidence digests. The editorial PDF, acquired archive, logs and build directories are local outputs. The [Phase 29 correction release](https://github.com/soyebmohammad03-dev/GENEVRA/releases/tag/phase-29-research-correction-1) is a historical prerelease at `85d1597cc30adf5e47dacea5a4aa0d2f43553a3e`. [Deposit metadata](../research/phase_29/deposit.json) records no assigned DOI.

## Reproduce and identify the PDF

Check the tracked inputs in a current checkout with `(cd docs/publication && shasum -a 256 -c SHA256SUMS)`. For exact builds, use a fresh checkout and output directory. The verified platform is macOS arm64 with uv, Python 3.12.15, NumPy 2.5.4 and the [replay lock](../research/phase_23/requirements-macos-arm64.txt). Put TeX Live 2026 with pdfTeX 1.40.29 and BibTeX 0.99e on PATH. The JSS scripts require curl, unzip and the official template with its pinned digest.

```sh
git clone https://github.com/soyebmohammad03-dev/GENEVRA.git
cd GENEVRA
git switch --detach 9c1ff41d264dccf958dad4dd872b0a1f2f544395
out=$(mktemp -d)
sh scripts/verify_publication_candidate.sh render "$out/frozen"
sh scripts/reproduce_editorial_manuscript.sh "$out/editorial"
shasum -a 256 "$out/frozen/research/final/GENEVRA-manuscript.pdf" \
  "$out/frozen/jss/manuscript.pdf" "$out/editorial/manuscript.pdf"
```

Use `replay` in place of `render` for full frozen reproduction from the registered archive. The replay checks the archive and all member digests. For the previously audited ASCII submission software attachment, follow the [source preparation instructions](../model_repair/FINAL_CLOSURE/JSS_SOURCE_COMPLIANCE_FINAL.md) at the same pinned revision. The historical source inventory compares the exact files from that revision. Use current `main` for the maintained runtime distribution.

The generic `genevra verify-evidence` command checks a curated package on disk. It rejects absolute paths, parent traversal and targets that resolve outside the package, including symlink escapes. Run it on a stationary, trusted package tree. Canonical checks do not protect against concurrent filesystem replacement or authenticate a manifest. The official replay capsule uses its separate digest and extraction validation.

## Frozen findings and scope

Shared blindness gave 0/512 target coverage, 180/512 false certificates per run, and 180/180 false among issued. The simultaneous upper bound of 40.73% applies to false certification **per run**. The matched-cost useful-precision counts were 1/256 for the width proxy, 104/256 for paid-pilot cost-adjusted Neyman and 229/256 for equal spend. The registered proxy-minus-Neyman difference was −40.23 percentage points with a 95% Hoeffding interval of [−57.21, −23.26]. All 103 discordant pairs favored Neyman. All 17 adjusted secondary intervals included zero. Mean width is a descriptive summary. Useful precision requires coverage and the width cutoff in each replicate.

GENEVRA integrates a synthetic benchmark and a verification framework for statistical certification under shared sampling-frame undercoverage. The statistical methods build on established work. The [claim audit](../model_repair/FINAL_CLOSURE/SCIENTIFIC_CLAIM_AUDIT_FINAL.md) records the negative allocation result, internal computational reproduction and limits on generalization. Field effectiveness and external researcher reproduction remain unestablished. Exact replay applies to the pinned platform. [Numerical reproducibility audit](../model_repair/FINAL_CLOSURE/NUMERICAL_REPRODUCIBILITY_FINAL.md)

Before submission, complete the [author and rights checklist](AUTHOR_AND_RIGHTS.md). Use the selected conference's template and artifact instructions.
