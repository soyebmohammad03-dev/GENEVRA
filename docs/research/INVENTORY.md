# Repository and capability inventory

The inspected starting research commit was a5dd134429b5a76cfe45e67bcc15b315dc23e57c with 376 tracked files. The local workspace also held historical uncommitted phases. The public integration imports immutable replay copies through the archive rather than staging those working-tree changes. Enumerate exact tracked paths with `git ls-tree -r --name-only <commit>`. The Phase 20 archive's SHA256SUMS enumerates its replay payload and PROVENANCE.json records source bundle digests.

| Directory | Responsibility | Implemented or evaluated | Evidence boundary |
|---|---|---|---|
| src/genevra/ | Importable simulator and research algorithms | Grid environments, controllers, within-lifetime learning, mutation, reproduction, lineage, ecology, metrics, analysis and CLI. Phase 19 coverage envelope and budget planner are on the research branch. | A software capability and passing tests do not validate a scientific construct. |
| experiments/ | Reusable entry points and explicit study configurations | Baselines, controlled comparisons and coverage-envelope runner. Frozen legacy phase runners live inside their own source snapshots. | Phase-local configuration and eligibility matter. |
| research_evidence/ | Committed original evidence with manifests | Configs, seeds, data, derived tables, figures, reports and research-question records. | The original claim gates are authoritative for that corpus. |
| notebooks/ | Auditable interpretation from saved outputs | One cross-phase notebook, executed in an isolated kernel. | Descriptive diagnostics and analytic sensitivity. No new acquisition. |
| results/ | Destination for local generated outputs | Output location for experiments; durable artifacts use versioned manifests and release assets. | Keep large generated datasets and transient files out of Git. |
| docs/ | Architecture, protocols, scientific claims and reviewer guidance | Original simulator documentation, Phase 19 extension, and this integration layer. | Earlier local reports and frozen bundles are preserved separately. |
| configs/, scripts/, tests/, .github/ | Configuration, verification, regression tests and CI | Existing simulator configs and quality workflows. New integrity-checked archived replay entry point. | Archived analyses are verified separately from checkout CI. |

## Scientific classification

- **Implemented and tested.** Simulator and controller features have software and pipeline checks. The historical evidence and claim matrix report which scientific comparisons actually ran. See the [original claim matrix](../final_claim_matrix.md) and [quality gate](../final_research_quality_gate.md).
- **Measured within the simulator.** The early controller studies investigated paired outcomes, repeatability, founder clustering and reference-label feasibility. None of the 96 candidate references qualified in Phase 7. These results motivated the later synthetic studies rather than validating the assay.
- **Synthetic with known law.** Phases 11–16 and 18 and the Phase 19 extension evaluate precision, calibration and certification under declared sampling laws. Independent replicate means a synthetic run. Phase 17 and the Phase 19 audit reconstruct earlier results. The indexed phases report both passes and failures.
- **Externally validated.** No independent empirical measurement validation or external peer review is established for this program.
- **Unverified.** Representative real reference access, external omission bounds, costs, generalizability, biological labels, causal claims and a validated biological endpoint.
- **Overlap.** Historical band calculations, input hashing, output routing and shell wrappers recur in several snapshots. They are frozen for replay. Phase 20 shares archive selection, integrity and dispatch at the integration boundary without changing the archived algorithms.
- **Distinct engineering contribution.** A linked set of frozen benchmarks separates sampling precision, identification, and policy value when both information access and the acquisition package are specified. The algorithms use established probability and optimization. The exact stress comparisons are project-specific.

Phase numbering in the original README refers in places to simulator feature milestones. The archive index uses measurement-study phase labels. The initial research audit and the model-repair pilot precede the numbered measurement studies.
