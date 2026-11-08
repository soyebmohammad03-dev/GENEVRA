# JSS submission compliance matrix

Reviewed against the [author guidelines](https://www.jstatsoft.org/authors), [style guide](https://www.jstatsoft.org/style) and [submission instructions](https://www.jstatsoft.org/guides/submission). The evidence applies to this candidate package.

| Requirement | Status | Evidence or remaining action |
|---|---|---|
| English article with JSS LaTeX style and submission PDF | Verified for draft | Official JSS article class and bibliography style, PDF, LaTeX and BibTeX. The draft uses the official `nojss` option to suppress publication branding. Final editorial style review and author fields remain open. |
| Title, abstract, keywords, article sections and citations | Verified for draft | Frozen abstract and claims, 12 author-year references and clickable identifiers, 5 figures and 4 tables. |
| Article and source files for submission | Prepared | Build stages the article, bibliography and figure source assets. Final attachments and portal fields require author review. |
| Installable and documented statistical software | Verified on one platform | Source installation, dependency resolution, CLI help, API help and worked reproduction on macOS arm64. The guide covers archive verification, architecture and troubleshooting. |
| ASCII, human-readable software source and formatted help | Engineering open | LaTeX and bibliography are ASCII. The full frozen research source tree includes Unicode notation. Review the final upload source inventory, any needed ASCII-compatible packaging, and formatted help coverage beyond the documented workflow. |
| GPL-compatible license | Author and engineering open | The repository uses MIT. Confirm all submitted code and other materials, including third-party contents and redistributable dependencies, against journal terms. |
| Availability via a standard software repository where practical | Open recommendation | Public Git and archived benchmark inputs are available. Standard package-index distribution has not been established. |
| Replication code, data and exact reproduction on at least one disclosed platform | Verified internally | Standalone driver, pinned environment and verified archive. The preparation record distinguishes frozen replay and JSS typesetting. Exactness beyond macOS arm64 is unverified. |
| Useful statistical software and comparison with similar implementations | External evidence and editorial assessment open | Documented method and interface comparison provided. Practical added value and independent use have not been demonstrated. |
| Empirical illustration where applicable | External evidence open | Worked synthetic example provided. Applicability and need for a credible empirical illustration remain for editorial and author assessment. |
| Submission declarations and author identity | Author action open | [Checklist](AUTHOR_CHECKLIST.md) and [unsigned cover letter](COVER_LETTER.md). Confirm contributor details, rights, disclosures and declarations. |
| Size limit and review delivery | Final portal check open | Current guide gives a 50 MB file limit and an external-link procedure. The replication archive and build products are separately referenced. Verify the final upload selections before submission. |
| Author fees | Policy verified | JSS states it charges no author fees. |

The preparation record establishes internal repeatability of the supplied workflow. A decision about submission still depends on author declarations, final source and license review, and evidence that the software is useful to researchers outside the project.
