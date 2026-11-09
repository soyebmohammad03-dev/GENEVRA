# External reproduction challenge

Status **awaiting an independent researcher**. The recorded executions were internal. Start from a new checkout and retain outputs in a separate directory. The exact replay target is macOS arm64, CPython 3.12.15, the pinned NumPy 2.5.4 environment and TeX Live 2026 with pdfTeX 1.40.29 and BibTeX 0.99e. TinyTeX-1 v2026.11 was used. Put its binaries on PATH. Git, uv, curl and unzip are required.

```sh
git clone --single-branch --branch research/publication-development https://github.com/soyebmohammad03-dev/GENEVRA.git
cd GENEVRA
git rev-parse HEAD
out=$(mktemp -d)
sh scripts/verify_publication_candidate.sh replay "$out/challenge"
(cd "$out/challenge" && shasum -a 256 -c SHA256SUMS)
```

The full replay fetches the [frozen release input](../../research/archive.json), verifies the whole archive and each of its 1,513 payload members, and creates a pinned Python environment. It runs the existing registered calculations and verifies the receipt, figures, tables and PDFs. The JSS builder fetches the official template archive and checks its pinned digest. A `render` invocation in a different fresh output directory checks the existing publication and TeX output without running the frozen benchmark.

The expected results include 0/512 target intervals covering the shared-blind target, 180/512 false certificates per run, 180/180 false among issued and the 40.73% simultaneous per-run upper bound. The primary comparison is 1/256 versus 104/256 versus 229/256, with paired proxy-minus-Neyman difference -40.23 points and interval [-57.21, -23.26]. Compare the exact [expected receipt](../../research/phase_29/rendered/audit-receipt.json). The JSS PDF should match the [frozen candidate](../../research/phase_29/jss/manuscript.pdf). Expect exit zero and matching SHA-256 output.

If acquisition fails, compare the URL, size and digest with the archive record. The underlying `scripts/reproduce_final_research.sh` also accepts a verified local copy of the archive as its second argument. The JSS build supports an offline official template via `JSS_TEMPLATE_ZIP`. Keep unsuccessful logs and use a new output directory for retries. Record unsupported environments or deviations separately. A different baseline simulation on Linux is a known portability observation and separate from this challenge.

## Researcher feedback template

- Reviewer identifier and relationship to the project, if any
- Commit, hardware, OS, Python, dependency versions and TeX tool versions
- Exact command, mode, elapsed time, and exit status
- Output hashes and whether each expected result matched
- Any clarification, platform changes or instructions needed
- Permission to quote or disclose your feedback, if applicable

## Discrepancy report template

- First observed difference and the smallest command that reproduces it
- Expected value or digest and actual value or digest
- Affected files or assertion and the relevant log lines
- Input archive hash and local environmental deviations
- Whether a clean retry produced the same discrepancy

Share the report and non-sensitive logs with the author through the repository's issue tracker or a mutually agreed channel. Preserve local copies of the original logs and receipts. Attribute the reproduction to the researcher only after they confirm the record.
