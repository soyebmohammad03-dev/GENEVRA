# Partner-independent operations and data dictionary

## Required capabilities

The partner must support physical access, independent roster custody and area audit, probability draws, traceable field handling, blinded laboratory measurement, finance records and approved export of aggregates. The custodian cannot report to either channel's acquisition lead for frame decisions. Assign separate development, acquisition, reference, QA and finance responsibilities, with a conflict declaration and an independent adjudicator. A single vendor may supply logistics only if role separation, file access and audit independence are demonstrable. No partner or authorization has been secured.

## Field-operation and quality checklist

- Before deployment, sign the scope and data-sharing terms, confirm land access and sampling permits, register adverse weather and safety stops, and record retention and release approvals. Resolve eligibility and duplicates blind to outcomes. Draw selections with the registered randomization, hash and escrow the lists.
- At selection, preserve the full roster and inclusion probabilities. Do not swap unreachable or unsafe sites. Record attempts, access failure, missed window, QC failure and protocol deviation separately from ineligibility adjudicated before draw.
- At field visit, use masked sample IDs, one time window, a traceable split, standard instrument checks and chain of custody. Log measurements in the permitted controlled workspace.
- At lab, apply prespecified calibration, blanks, duplicates, detection limits, tolerance and disagreement resolution. Record QC and secondary adjudication; do not force borderline labels. Do not reveal channel or policy decisions.
- Before scoring, reconcile all attempts, reference strata and cost lines. Freeze acquisition-only decisions. Compare package digests and charged cost. Open reference only after custody confirms the lock. Report discrepancies and deviations. Gate the release on disclosure review.

## Data dictionary

The following is a proposed schema. No records were collected. Use opaque study-generated IDs. Keys are scoped to protocol version and episode. Numeric quantities include units and validity flags.

| Record | Required fields | Rules and provenance |
|---|---|---|
| Episode | episode_id, protocol_version, season_window, roster_version_hash, design_stratum, freeze_receipt, deployment_status | One policy-level analysis unit. Exact geography remains at the custodian. Cluster identifier if crews or watersheds recur. |
| Roster unit | unit_id, episode_id, reach_week_key, eligibility_status, eligibility_reason, source_version, duplicate_group, adjudication_version | One eligible reach-week. Preserve prior versions. Protected geometry is separate. |
| Operational crosswalk | unit_id, channel_a_status, channel_b_status, recruitability_a, recruitability_b, match_status, adjudication_code | Distinguish eligible available, unavailable, uncertain and not matched. No off-roster unit is silently assumed absent. |
| Area audit | segment_id, area_frame_version, selection_probability, eligible_roster_matches, new_eligible_units, disputed_units, audit_disposition | Segment selected independently of both operational channels and outcomes. Retain cap derivation and uncertainty. |
| Reference draw | unit_id, stratum_id, roster_size, sample_size, inclusion_probability, draw_receipt, reference_label_status | Positive design probability for each target stratum. Selection lists and observed outcomes are escrowed until release. |
| Attempt/QC | sample_id, unit_id, attempt_index, window_status, disposition, assay_version, qc_code, label, adjudication_reason | Label is positive, negative or unresolved. No personal names, addresses, staff identifiers, precise sensitive locations or free-text identifying details. |
| Decision | episode_id, policy_version, package_hash, charged_cost_units, anchor, tolerance, interval_low, interval_high, issued, decision_digest | Freeze before reference release. Record all policies including refusals. |
| Cost line | episode_id, package_hash, role, cost_category, quantity, unit, unit_cost, currency, allocation_rule, receipt_code | Separate recurring from setup and evaluation from acquisition. Use integer minor currency units for charges. No invoice PII in research output. |
| Deviation | episode_id, version, stage, code, scope, disposition, timestamp_receipt | Append only. Changes before outcomes can require a new registration; changes after outcomes are labeled deviations. |

### Cost-recording template

One line per approved expense or staff-time activity. Copy the header into the partner's governed ledger. Enter setup allocation separately and reconcile totals per package. Attempted but failed visits still cost money.

```csv
episode_id,package_hash,role,cost_category,quantity,unit,unit_cost_minor,currency,allocation_rule,receipt_code
```

Use categories such as frame setup, outreach, permit, travel, attempted visit, completed sampling, lab, QC, computation, reference adjudication and archiving. Register wage conversion and billing boundaries in advance. Do not publish unredacted invoices.

## Governance and ethics

Collect no personal or sensitive data in the research dataset. Custodian holds exact locations only where approved and operationally necessary, and excludes protected sites from public records or releases aggregates subject to policy. No participant recruitment is proposed. Site access, environmental sampling permission, safety rules and any institutional or local ethics review must be determined by the partner before deployment. If the design starts involving people or identifiable information, halt and obtain the required review and consent decision before collection. This package grants no ethics approval, permit or institutional authorization.

The data-sharing agreement should specify parties and purpose, independent role ownership, permitted records and access controls, approved transfer and encryption, retention and deletion, dispute and breach procedures, disclosure review, withdrawal, publication of permitted aggregates and verification access. Maintain the data dictionary and consent or permit decisions in versioned governance records. Do not publish protected coordinates or identifiable materials in GitHub.
