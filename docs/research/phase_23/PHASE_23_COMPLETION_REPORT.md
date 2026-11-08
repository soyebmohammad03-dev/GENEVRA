# Phase 23 completion report

**Ready for external technical review. Journal submission, field recruitment and confirmatory validation remain on hold.** The current contribution is a bounded, reproducible feasibility benchmark. The internal statistical, experimental and applied assessments are simulated reviews with distinct recommendations. No reviewer or research partner was contacted, no new scientific acquisition was undertaken, and no new synthetic campaign was run. The replay reexecuted earlier frozen simulations.

## Scientific findings and limits

- In the frozen shared-blindness case, 180/512 runs gave false certificates and 0/512 achieved mean coverage. The simultaneous one-sided upper bound was 40.73%. No threshold call was wrong in that case. All three reported matched utility intervals included zero.
- A supplied valid cap rescued large-omission coverage from 0/512 to 512/512 with zero precise intervals in the tested comparison. In the separate small-omission case, at equal stipulated spend the planner achieved 10/512 covered and precise versus 450/512 for the equal-spend comparator.
- With a fixed reachable law, unrestricted hidden tail rate and a defensible omitted-mass cap, the cap times the fixed score span is a width floor. Sampling more reachable cases leaves that floor unchanged.
- The Census reconstruction is external descriptive evidence of net coverage discrepancy. It cannot identify gross omitted mass or adjudicate a GENEVRA policy.
- The literature establishes the component ideas, including real field examples of independent spatial frames uncovering omissions. The potential contribution is the specific replayable stress suite and its matched comparisons across three endpoints. Originality and practical usefulness need external assessment.

See the [claim-evidence matrix](CLAIM_EVIDENCE_MATRIX.md), [literature audit](LITERATURE_AND_NOVELTY.md) and [revised manuscript foundation](MANUSCRIPT_FOUNDATION.md).

## Execution and validation

| Scope | Result |
|---|---|
| Full existing working-tree tests | 1,013 passed, zero failures and skips, 94% reported coverage. Pytest 245.95 s, 246.40 s command wall, maximum RSS 271,826,944 bytes. |
| Working-tree static checks | Ruff lint passed and all 501 files formatted. Strict mypy passed for 174 source files. |
| Clean public-tree tests | 748 passed, zero failures and skips, 94% reported coverage. Pytest 215.31 s, 216.35 s command wall, maximum RSS 154,451,968 bytes. |
| Clean public-tree static checks | Ruff lint passed and all 346 files formatted. Strict mypy passed for 154 source files. |
| Evidence verifier | Passed on both trees with no checksum mismatch, missing reference, orphan or seed split overlap. |
| Public archive | Ten entries verified with archived and separate reconstruction checks. 127.55 s wall, maximum RSS 405,897,216 bytes. |
| Figures and design receipt | Notebook identification figure, Phase 19 envelope SVG, Census JSON and PNG, and Phase 22 design receipt all byte-identical. |
| Historical integrity | 18,143 inventoried files SHA-256 checked with zero mismatches. All 29 inventoried historical ZIPs passed CRC. All 190 preexisting tracked-change or untracked status entries were preserved. The root README receives a navigation entry and audit wording clarification. |

The verification used macOS 27.0.1 arm64 and CPython 3.12.15. The [reproduction receipt](reproduction-receipt.json) records source, archive, input and expected output identities. The [reproduction guide](REPRODUCIBILITY.md) records commands and dependency versions. The exact environment for archived replay was a fresh venv and an export of the public parent Git tree. Working-tree-only history remains outside this release.

## Delivery scope

Root `README.md` links to Phase 23 and distinguishes internal audit from external review. The new directory contains the review index, claim-evidence matrix, literature audit, three simulated reviews, qualification and collaboration documents, publication decision, manuscript foundation, reproducibility guide, two pinned dependency lists, receipt, this report and SHA-256 manifest. No simulator source, test or historical artifact was changed by Phase 23.

## Next evidence

The [decision gates](PUBLICATION_DECISION.md) prioritize the reproducible benchmark and systems route, with a scoped negative feasibility technical report as fallback. Invite an external researcher to replay the archive, assess the closest benchmark and audit comparator access. A prospective partner would separately need an independent custodian and area frame, off-channel reference access, blinded and demonstrably reliable measurement, cost and nonresponse logs, permissions and data governance. Even with those prerequisites met, twelve episodes would screen operations only. Zero adverse events would still leave a 27.82% one-sided upper bound under the proposed assumptions, above the 5% safety gate. The next field decision would require the operational gates and a separately powered design.
