# Final editorial audit

The [editorial manuscript](manuscript.tex) corrects four repeated narrative author names, clarifies the two false-certification denominators and the per-replicate width criterion, and places figure and table references in their relevant sections. It preserves the frozen research narrative, negative allocation result and synthetic scope.

The full source and all 11 rendered pages were reviewed. The introduction distinguishes target identification from sampling precision, the research questions lead to the registered comparisons, and the abstract and conclusion agree with the reported endpoints. The bibliography starts on a fresh page. Sensitivity displays now share a page with the surrounding article text. The build reports no unresolved references or overfull boxes. Two underfull vertical boxes reflect sparse page layout. The pending affiliation remains on a separate last page and needs an author-final recheck.

| Audit | Record |
|---|---|
| Exact prose and layout changes | [Corrections](MANUSCRIPT_CORRECTIONS.md) |
| All 12 citation keys and links | [Citation audit](CITATION_AND_REFERENCE_AUDIT.md) |
| All five figures and four tables | [Display audit](FIGURE_TABLE_AUDIT.md) |
| Counts, risk denominators and intervals | [Mathematical audit](MATHEMATICAL_CONSISTENCY_AUDIT.md) |
| Journal and author decisions | [Submission checklist](JSS_SUBMISSION_CHECKLIST.md) and [author actions](FINAL_AUTHOR_ACTIONS.md) |

## Rebuild and validation

From the repository root with the pinned TeX environment on PATH:

```sh
sh scripts/reproduce_editorial_manuscript.sh NEW_OUTPUT
```

The command reuses the frozen JSS build, stages the editorial LaTeX as a separate candidate, compiles it and prints checksums. It uses the original 12-entry bibliography and five figure assets. The editorial PDF SHA-256 with pdfTeX 1.40.29 and BibTeX 0.99e is `dd8747c8964c6e7bbbabadbb6ec51a33faa31bcd486f56bd1eeecaecc4e0ffa5`. It is a local review build. The public source and script provide its reproduction route.

On macOS arm64 with Python 3.12.15, 49 targeted reference, benchmark-validation and reproducibility-contract tests passed in 0.40 seconds, with zero failures and skips. The publication-only reconstruction matched the original technical PDF and audit receipt byte for byte. The editorial checks matched the 12 bibliography destinations, ordered citation keys, unchanged figure bytes, numerical table bodies and nine resolved display labels. Independent calculations confirmed the paired interval and simultaneous binomial bound. The frozen benchmark campaign was not rerun.

## Verdict

| Area | Verdict |
|---|---|
| Engineering completeness | COMPLETE |
| Software distribution | COMPLETE for the verified candidate |
| Scientific reproducibility | DOCUMENTED LIMITATION. Exact internal evidence on the pinned environment. |
| Scientific contribution | DOCUMENTED LIMITATION. Synthetic benchmark and numerical verification with limited transfer claims. |
| Manuscript quality | COMPLETE for editorial review. Author block pending. |
| Journal formatting compliance | AUTHOR ACTION REQUIRED for final attachment and author-block review. |
| Author declarations | AUTHOR ACTION REQUIRED |
| Independent validation | EXTERNAL VALIDATION REQUIRED |
| Overall submission readiness | AUTHOR ACTION REQUIRED and EXTERNAL VALIDATION REQUIRED. Hold submission. |
