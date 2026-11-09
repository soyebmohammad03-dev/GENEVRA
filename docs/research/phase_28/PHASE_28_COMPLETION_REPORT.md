# GENEVRA Phase 28 completion report

**Decision.** The manuscript and publication package are prepared for independent technical review. Journal submission remains on hold. The contribution is a reproducible, evidence-linked benchmark of certification failures under shared frame undercoverage. Established statistical procedures support the benchmark. No external reviewer, new scientific data, or new evaluation scenario entered this phase.

## Manuscript and evidence

The [nine-page manuscript](rendered/GENEVRA-manuscript.pdf) preserves the negative allocation result in its abstract and results. Its [source](MANUSCRIPT.md), [supplement](SUPPLEMENT.md) and [bibliography](REFERENCES.md) state the target, cost model, interval construction and two certificate rules. All three allocation methods covered every target in the primary cell. Useful precision remained 1/256 for the width proxy, 104/256 for paid-pilot Neyman and 229/256 for equal spend. The paired proxy-minus-Neyman interval was −57.21 to −23.26 percentage points around −40.23. The paper distinguishes local benchmark comparisons from general efficiency claims.

The builder derives five figures and four tables from a frozen [evidence extract](rendered/evidence.json), with two labeled conceptual diagrams and a labeled exploratory sensitivity figure. Manuscript result tokens, denominators and source hashes are checked before rendering. The [build receipt](rendered/build-receipt.json) pins the source and outputs. The publication package includes software/environment notes, citation metadata, submission templates, prospective venue guidance and three internal reviewer perspectives.

## Audit and revisions

The statistical review separated unconditional and conditional false certification, the different Phase 18 and Phase 25 certification rules, weighted width components and per-replicate classification. The novelty review narrowed the contribution to the benchmark and verification path. The experimental review identified exogenous caps, charges that omit field acquisition costs, and the difference between separate code and external evaluation. [Unresolved objections](REVIEWER_READINESS.md) remain visible.

Journal of Statistical Software is a conditional software route if external use demonstrates added value. Survey Methodology and JSSAM are plausible only with stronger survey-design relevance or independently validated evidence. Venue preparation and disclosures remain drafts. The [venue assessment](VENUES.md) identifies the requirements and verified cost information. No submission occurred.

## Verification

The full existing suite passed 1,094 tests in 249.44 seconds, with no failures or skips and 94% reported coverage. Ruff lint and formatting, strict mypy in the configured source scope and evidence verification passed. The build uses CPython 3.12.15, Matplotlib 3.11.2 and ReportLab 4.4.9 in the pinned macOS arm64 environment. A separate local rebuild matched the PDF, figures, tables and evidence receipt byte for byte. All rendered pages were visually inspected. Extracted text checks covered numeric result strings, figure/table captions and citation keys. Bibliographic records and stable identifiers were checked against publisher, agency and registry records. The Neyman reference uses the article pages 558–606 for its publisher DOI, separate from the discussion pagination. Cross-platform rendering is outside the byte-equality guarantee.

All 18,143 inventoried historical hashes matched and 29 historical ZIPs passed CRC. The root README now links the new package and states the submission status. The earlier tracked and uncommitted work remains separate. The [reproduction command](README.md) runs the full frozen challenge before rebuilding and comparing the publication directory.
