# Final candidate artifact inventory

The candidate references immutable publication assets in place and acquires the historical archive through its verified upstream location. It carries no new copy of a mixed-rights archive.

| Component | Candidate source |
|---|---|
| Manuscript | [JSS PDF](../../research/phase_29/jss/manuscript.pdf), [LaTeX](../../research/phase_29/jss/manuscript.tex), [BibTeX](../../research/phase_29/jss/references.bib), [frozen citation audit](../../research/phase_29/BIBLIOGRAPHY_AUDIT.md) |
| Figures and tables | [Five frozen figures](../../research/phase_28/rendered/figures) and [four machine-readable tables](../../research/phase_28/rendered/tables). The JSS builder stages the five PNGs with the manuscript and bibliography. |
| Supplementary methods and claims | [Supplement](../../research/phase_29/SUPPLEMENT.md), [statistical review](../../research/phase_29/STATISTICAL_REVIEW.md), [claim audit](SCIENTIFIC_CLAIM_AUDIT.md), [benchmark receipt](../../research/phase_29/rendered/audit-receipt.json) |
| Software source and help | [Source tree](../../../src/genevra), [build configuration](../../../pyproject.toml), [installation and CLI guide](../phase_30/INSTALLATION_VALIDATION.md), [source inventory](SOURCE_ENCODING_INVENTORY.md) |
| Replication inputs and instructions | [Archive acquisition record](../../research/archive.json), [external challenge](EXTERNAL_REPRODUCTION_CHALLENGE.md), [candidate verifier](../../../scripts/verify_publication_candidate.sh) |
| Comparators and submission documents | [Software comparison](../../research/phase_29/jss/COMPARISON.md), [draft cover letter](../../research/phase_29/jss/COVER_LETTER.md), [author declarations checklist](../../research/phase_29/jss/AUTHOR_CHECKLIST.md), [compliance matrix](JSS_FINAL_COMPLIANCE.md) |
| Rights and checksums | [Provenance audit](LICENSING_AND_PROVENANCE_FINAL.md), [Phase 31 manifest](SHA256SUMS), [frozen manuscript manifest](../../research/phase_29/jss/SHA256SUMS), [frozen evidence manifest](../../research/phase_29/FROZEN_SHA256SUMS) |

To assemble the typesetting directory, run the candidate verifier in render mode. Its JSS subdirectory contains the source, bibliography, figures and reproducible PDF. Its logs and receipts serve as the candidate reproducibility appendix. The software source remains a review candidate while the ASCII and rights gates remain open.
