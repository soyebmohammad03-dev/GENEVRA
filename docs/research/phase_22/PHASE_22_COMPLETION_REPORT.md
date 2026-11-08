# Phase 22 completion report

**Decision.** The prospective study package is ready for independent design review. The proposed 12-episode pilot is conditionally operationally feasible, with **NO-GO for recruitment today**. No independent partner, target frame, separately governed reference audit, lab commitment, permits or cost ceiling exists. No field observations or personal data were collected. The draft has not been registered or approved.

## Completed design and engineering

The [protocol](PROTOCOL.md) separates target enumeration, acquisition calibration and anchor certification. It specifies an independent custodian, area-based audit of the reference frame itself, channel linkage after roster freeze, probability reference sampling that includes the neither-channel stratum, and blinded assay adjudication. An independently justified off-frame mass bound is necessary for a full-target claim when coverage is incomplete. Unresolved outcomes widen the reference set and are adverse for issued certificates. Same-package and same-charge rules prevent information or cost advantages. Direct calibration is the primary comparator and GENEVRA can lose.

The [operations and data dictionary](OPERATIONS_AND_DATA_DICTIONARY.md) supplies field, governance, cost and stop/go instructions. The [registration draft](PREREGISTRATION_DRAFT.md) identifies operational values and permissions still missing. This is a protocol foundation, not an approved plan to collect data.

The code adds exact fixed-size SRSWOR reference inversion, unresolved completions and off-frame expansion, conservative adjudication, cost/package checks, one-sided safety limits and paired power sensitivities. It is a design-check module, not a field production pipeline. Six deterministic synthetic fixtures show correct reference scoring, detectable shared blindness, refusal with incomplete reference, and apparent correctness under a wrong cap. Two additional access/cost checks reject mismatched comparisons. No stochastic campaign ran. The [receipt](design_receipt.json) records all calculations.

## Pilot and power

With zero adverse events in 12 independent episodes, the 98% one-sided upper risk limit is 27.82%, above the 5% gate. The pilot can test real operations, reference feasibility and cost accounting. It cannot establish safety, superiority, general frame coverage or biological validity. The sample-size sensitivity uses illustrative assumptions only. Under IID episodes and 1% true adverse risk, n=209 with at most four events has about 94% power for the safety gate. At 2.5% risk the same plan has about 40% power. The paired usefulness margin is a separate constraint. Clustering, uncertain reference bounds and missing episodes can make these numbers inapplicable. See the [feasibility and sample-size analysis](FEASIBILITY_AND_SAMPLE_SIZE.md).

## Validation and preservation

| Check | Result |
|---|---|
| Full local suite | 1,013 passed in 249.71 seconds, zero failures or skips, 94% coverage |
| Clean public-tree focused validation | 16 passed, design receipt reproduced byte for byte |
| Static and evidence checks | Ruff lint and formatting, strict mypy and evidence verification passed |
| Independent arithmetic | Separate Decimal sums matched seven exact gate thresholds, 35 power values and seven zero-event bounds |
| Historical replay and notebook | All ten entries passed; four notebook cells executed; historical figure reproduced byte for byte |
| Historical integrity | 16,121 inventoried files byte-identical. All 21 prior ZIPs passed CRC. Root README received a navigation link. |

The reproducibility manifest covers the review documents and receipt. Numerical verification was performed locally, including a separate arithmetic implementation. No third-party review or empirical validation occurred.

## Scientific scope and delivery

The [publication foundation](PUBLICATION_FOUNDATION.md) separates completed synthetic evidence, the reconstructed Census diagnostic, this proposed study and evidence still unavailable. The strongest route remains a reproducible benchmark with negative feasibility results. Journal submission remains on hold. The next step is to obtain a qualified independently governed partner and demonstrate off-channel access and reference precision before recruiting.

The change adds one analysis module, one design-check experiment, 16 test cases, the Phase 22 review package and a README link. Earlier local edits and archived experiments were preserved. Delivery targets only the research branch.
