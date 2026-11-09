# Journal readiness decision

## Journal of Statistical Software requirements recheck

Current [author requirements](https://www.jstatsoft.org/authors), [submission guide](https://www.jstatsoft.org/guides/submission) and [style guide](https://www.jstatsoft.org/style) were checked again for this correction. Submission remains on hold.

| Requirement | Current status |
|---|---|
| English manuscript in LaTeX with JSS style files, submitted as PDF | The corrected PDF is a technical review copy built with ReportLab. A JSS LaTeX conversion and style check are outstanding. |
| Source code, ASCII, documented and installable | The public release includes human-readable code, a package configuration and run instructions. The rendering code includes Unicode notation, so an ASCII submission-source check and conversion, formatted help review and installable submission-package review remain open. Standard package-repository distribution is encouraged. |
| GPL or GPL-compatible licensing | The repository declares MIT. Review the full submission bundle and all bundled materials for license compatibility before submission. |
| Standalone replication material, exact results on at least one platform and platform disclosure | Phase 29 recorded the complete benchmark replay on macOS arm64. The correction checks the frozen-input publication build separately. Recheck the submission-formatted outputs and supplement once prepared. Cross-platform exactness remains unverified. |
| Scope and review | JSS emphasizes useful software and comparison with similar implementations, with empirical illustration where applicable. Independent use and demonstrated added value remain outstanding. |
| Uploads and fees | JSS states no author fees and a 50 MB upload limit. Recheck file sizes and portal requirements for the exact submission package. |


Publisher and agency requirements checked on 9 November 2026. A technical review package is ready. Journal submission remains on hold.

| Candidate | Scope and contribution fit | Method, software and data requirements | External evidence gate | Format and verified costs |
|---|---|---|---|---|
| Journal of Statistical Software | Conditional first route for the reusable benchmark and verification software. The existing allocator result is not a novel method | Compare with implementations of similar scope, document accessible software, and supply exact standalone replication with data and code. JSS asks for ASCII software source, a GPL-compatible license and installable software. It encourages a standard package repository where possible | Establish independent use, practical value and added functionality against the closest available software. Empirical illustrations are requested where applicable. Synthetic replication alone does not settle usefulness | JSS-style LaTeX manuscript and PDF. The current PDF is a technical review version. JSS reports no author fees. [Author requirements](https://www.jstatsoft.org/authors) |
| Survey Methodology | Substantive fit for coverage, frame design and data integration if an independent case shows a practical insight | Demonstrate new relevant insight or an adaptation that solves a relevant problem. A simulation can form part of the evidence. Supply exact frame and target definitions and reproducible methods | Independent scrutiny of relevance and preferably an independently audited field or survey-design case | Regular article or substantially shorter note. Public electronic journal. No APC amount was verified in reviewed guidance. [Scope](https://www150.statcan.gc.ca/n1/pub/12-001-x/index-eng.htm) · [Submission](https://www150.statcan.gc.ca/n1/pub/12-001-x/manuscripts-eng.htm) · [Reviewer criteria](https://www150.statcan.gc.ca/n1/pub/12-001-x/reviewer-examinateur-eng.htm) |
| Journal of Survey Statistics and Methodology | Fit for survey coverage and nonresponse with a compelling design application | Data and analytic-code availability, design disclosure and applicable complex-survey reporting. The [Dutch frame comparison](https://doi.org/10.1093/jssam/smy016) illustrates the empirical relevance expected of an applied framing | Real frame and nonresponse dispositions, independent outcomes and actual acquisition costs before an empirical claim | Methodological article. Standard license or optional paid open access. Exact current optional charge and institutional eligibility were not verified. [Author requirements](https://academic.oup.com/jssam/pages/General_Instructions) |

Fallback is a scoped negative feasibility technical report. No additional journal is recommended without a stronger scope match. Author declarations and institutional details in the [submission materials](../phase_28/SUBMISSION_MATERIALS.md) must be confirmed before any submission. Prospective held-out and empirical work are separate research evidence, rather than deliverables of this final engineering phase.

## Cover letter for the conditional software route

Dear Editors of the Journal of Statistical Software,

Please consider “When sampling frames share a blind spot: a reproducible benchmark for population-mean certification” as a statistical software contribution. GENEVRA supplies a frozen synthetic benchmark and separately implemented reference calculations for distinguishing population coverage, useful precision, and anchor certification under shared undercoverage. Its matched-cost primary comparison shows that the width-proxy allocation underperforms a paid-pilot variance baseline. The artifact preserves that negative result and makes the raw counts, costs and reference decisions reproducible with a standalone command.

The manuscript applies established methods and scopes its contribution to the benchmark and verification workflow. The corrected research release contains synthetic data, a pinned environment, and scripts for rebuilding the results and publication materials. Before sending this letter, attach the JSS-style LaTeX manuscript and PDF, checked software source and help, and the exact replication materials.

Soyeb Mohammad

**Prepared for later use.** This letter has not been sent. Before submission, update it with verified external-use evidence and the exact JSS-formatted source and replication asset. Confirm author declarations, affiliations, and venue-specific software requirements.
