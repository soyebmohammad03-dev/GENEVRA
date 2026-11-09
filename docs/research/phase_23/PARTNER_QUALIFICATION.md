# Partner qualification and decision record

**Recruitment is NO-GO.** No institution is named, contacted, evaluated or committed. All criteria are currently unassessed.

Use a 0–2 score for each mandatory row. Score 0 if evidence is absent or contradicted, 1 for a documented plan, and 2 for verification by a designated custodian or independent reviewer. Record evidence locator, version, reviewer role, date, restrictions and unresolved deviations next to each score. Do not compensate for a failed gate with strengths elsewhere. Each mandatory row needs score 2 and signed institutional authorization before reviewing a pilot launch.

| Mandatory gate | Minimum verifiable evidence | Current score |
|---|---|---|
| Independent enumeration | Custodian with segregated roles, dated hydrographic source, registered eligibility rules and duplicate resolution demonstrated on a roster extract | Unassessed |
| Reference coverage | Separate probability area-audit frame with explicit inclusions and bounded missing counts, plus a feasible probability sample reaching neither-channel units | Unassessed |
| Reference measurement | Independent lab, assay specificity and error documentation, split-sample capacity, blinded custody, retest and unresolved label rules | Unassessed |
| Blinding and freeze | Access-role matrix and witnessed draw, timestamped policy lock before reference release, breach and amendment procedures | Unassessed |
| Nonresponse | Reason codes and audit trail for refusals, access failures, unsafe attempts, pending and unresolved labels, with no replacement after seeing outcomes | Unassessed |
| Cost and capacity | Written acquisition ceiling and a demonstrable ledger for acquisition, independent reference, staff time and failed visits | Unassessed |
| Governance | Approved data-use and aggregate release terms, access logs, retention and deletion policy, ownership and conflict disclosures | Unassessed |
| Institutional and field authorization | Written permits and safety sign-off, institutional ethics determination when applicable, approved lab and escalation procedures | Unassessed |

## Technical specification

The [Phase 22 data dictionary](../phase_22/OPERATIONS_AND_DATA_DICTIONARY.md) is the schema baseline. Join episode → reach-week → reference attempt with custodian pseudonyms and a separately held spatial crosswalk. Episode fields include watershed-season block, geography version, eligibility/assay protocol digest, policy package digest, immutable decision timestamp, code commit, cost currency, reference-family allocation and release status. Reach-week fields include eligibility, frame inclusion, A/B membership and actual reachability, frozen stratum size, draw probability, disposition and nonresponse. Keep the area-audit segment ID and design inclusion separate from the roster sampling inclusion.

Reference records include blinded sample ID, chain of custody, assay and threshold version, replicate identifiers, QC flags, adjudicated outcome or unresolved status, and reason and lock timestamps. Area-audit records carry assigned units, missing/extra counts, disposition and count bounds for unvisited segments. Record numerator and denominator evidence for any claimed omission cap. Cost rows link package or reference job to category, quantity, rates, failed attempts and approved exceptions. Freeze typed units, currency, timestamp zone, missing-value codes and join cardinality before collection.

Custodian keeps identities, exact locations and blind crosswalk. The policy team receives only the frozen acquisition package. The lab receives only blinded IDs and assay requirements. The external evaluator receives the frozen decisions and permitted reference tables after lock. Publish only approved aggregates and allowed deidentified extracts. Version all access, roster amendments, exclusions and release decisions.

## Questions for prospective collaborators

1. Who can enumerate reach-weeks without A/B input, and how would an independent mapper audit the missing denominator?
2. Which eligible strata cannot be visited and how will their counts and outcomes be bounded?
3. What documented assay error and borderline classifications would remain after blinded repeat measurement?
4. How can the team prove that acquisition decisions were sealed before reference results were accessible?
5. What records explain unavailable visits and failed measurements without replacing unfavorable units?
6. What ceiling covers staff, permits, sampling, laboratory work and failed attempts? Which costs belong to shared evaluation?
7. What approvals and disclosure rules govern locations, samples, data release and oversight?

## Decision path

Score each row with independent evidence and record a signed decision. Failure to audit the missing denominator confines claims to the enumerated frame or blocks the pilot. Absent approvals, cap, safe access or separate references, stop before enrollment. If all prerequisites pass, submit a prospective operational pilot registration. Only the [frozen Phase 22 operational gates](../phase_22/FEASIBILITY_AND_SAMPLE_SIZE.md) can justify a later power review. Confirmatory approval requires a separate registration and justification.
