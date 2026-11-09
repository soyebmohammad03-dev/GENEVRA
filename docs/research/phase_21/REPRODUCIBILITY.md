# External reviewer reproduction

The Phase 21 directory is the review package. It includes the protocol, data assessment, frozen cell and row provenance, script, expected JSON and figure, and SHA-256 manifest. The Census source inputs remain at the publisher. No restricted data or large raw datasets are redistributed.

From a clean research-branch checkout:

```sh
d="$PWD/docs/research/phase_21"
out=$(mktemp -d)
(cd "$d" && shasum -a 256 -c SHA256SUMS)
curl -fLsS https://www2.census.gov/programs-surveys/popest/tables/2020/2020-demographic-analysis-estimates/Table-3_PES-sex.xlsx -o "$out/Table-3_PES-sex.xlsx"
curl -fLsS https://www.census.gov/newsroom/press-releases/2024/undercounts-overcounts-children-2020-census.html -o "$out/2024-release.html"
python3 "$d/reconstruct.py" "$out/Table-3_PES-sex.xlsx" "$out/2024-release.html" "$out/derived.json"
cmp "$d/census_diagnostic.json" "$out/derived.json"
```

The workbook must match its recorded SHA-256. The HTML contains page chrome and may change without changing data. Its retrieved digest is retained for provenance. The parser verifies the national row values and the numerical result exactly. If the publisher changes the selected values or makes the source unavailable, stop and record the discrepancy. Do not substitute a different vintage. To recreate the figure, rerun with a new JSON path and add `--figure "$out/census_diagnostic.png"` using Matplotlib 3.11.2 from the [pinned research replay environment](../README.md). The workbook parser and count reconstruction otherwise use the standard library only.

For independent numerical checking, read cells C5:E5 of the workbook's Table 3 with another spreadsheet reader, and recompute 100 times (Census count divided by DA estimate minus one) from the national row of the April release. Verify both dates and the denominator. The project performed this cross-check using openpyxl 3.1.5, an alternate HTML parser and Decimal arithmetic. This is an independent implementation by the project, without external reviewer involvement.

Run the complete [Phase 20 public replay](../README.md) and [notebook](../../../notebooks/README.md) to verify the synthetic historical claims used by the manuscript. Check that a notebook rerun regenerates the identification-floor figure. Keep the external Census diagnostic separate from those synthetic studies. A third-party reviewer should return their hashes, commands, discrepancies, judgment of target comparability, and any conflict or independence limitations. A successful reproduction cannot resolve the absence of matched empirical policy outcomes.
