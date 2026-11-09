# Scientific dependency map

| Phases | Inputs, estimand and dependencies | Outputs, checks and boundary |
|---|---|---|
| 1–2 | Original simulator and experiment configuration, seeds, frozen evidence, and model-repair checks for metabolism, RNG isolation and paired parent-mutant outcomes | [Original corpus](../../../research_evidence/README.md) and local audit/model-repair archives. Replay includes later dependency slices. Software checks do not validate evolvability. |
| 3–5 | Founder, ensemble, mutation, shared parent and episode-panel keys. Paired controller-only scores, epsilon .60 and nested technical samples | Local frozen reports and arrays. Weak fraction repeatability and uncertain founder discrimination. Independent inference unit is founder where claimed. |
| 6–8 | Paired sampling changes, independent reference observations, identity controls, synthetic positives and analytical risk calculations | Local frozen bundles. Zero of 96 candidate references qualified. Control false-call behavior does not establish biological sensitivity. |
| 9–10 | Separate simulator feasibility and bounded precision / variance-reduction scenarios | Local frozen reports and bundles. Declared simulator estimands and synthetic precision are distinct from biological validity. |
| 11–13 | Archived snapshots and configs with bounded support, tail or residual rates, independent strata and synthetic known truth | Each capsule `reproduce.sh` reconstructs precision and coverage with phase-specific independent scalar or vector checks. Gain depends on valid identifying information. |
| 14–16 | Source/target shift, frame metadata, supplied weights, independent audit rates, support and access | Frozen case tables and raw checks in capsule. Weight errors, missing strata, and shared blindness are counterexamples. |
| 17 | Phase 15 and 16 verified data and separate access accounting | Reconstructs comparator availability and access asymmetry. Equal row count is insufficient. |
| 18 | `phase-18/raw/cells/*.json`, config, manifest and frozen source. Counts, cases, seeds, bounded confidence calculations, common package and tariff | Archived replicate arrays, rates, summary and contrasts. Main endpoints computed from raw counts and separately scored in Phase 24. No superiority or safety gate passed. |
| 19 audit | Phase 18 raw files and frozen analysis with a separate likelihood inversion and reconstruction | `phase-19/docs/verify_phase18.py`, checks all archived replicate arrays and summaries, including simultaneous safety upper bounds. |
| 19 extension | `phase-19-extension/raw.json`, freeze and config. Nested counts, weights, independent units, cap and support, tariff and two budgets | Envelope and width proxy estimates checked with separate long-double inversion, closed-form endpoints and exhaustive allocation. 18 cells, 9,216 paired replicates and 630 rates. |
| 20 | Public capsule SHA-256 and member inventory, pinned Python and scientific libraries, research notebook | Integrated ten-entry replay, archived analysis and linked figures. Earlier local artifacts are not all distributed. |
| 21 | US Census workbook and later public national counts | [Separate reconstruction](../phase_21/REPRODUCIBILITY.md). Descriptive net discrepancy only. |
| 22 | Proposed reach-week population and independent watershed-season units. Fixed synthetic fixtures and analytical design checks | [Prospective receipt](../phase_22/REPRODUCIBILITY.md). No field acquisitions or qualified partner. |
| 23 | Frozen results, literature, three simulated reviewer perspectives and partner gates | [External review package](../phase_23/README.md). Internal scrutiny only. |
| 24 | Public parent plus new scorer, verified capsule, published figure checks and pinned environment | Clean replay, independent decision aggregation, adversarial receipts and competitor submission schema. No new scenarios or empirical validation. |

The [frozen experiment index](../EXPERIMENT_INDEX.md) gives the individual replay entrypoints for Phases 11–19. The original and early repair files retained in the local research workspace are outside the public capsule. No full public replay of Phases 1–10 is claimed.
