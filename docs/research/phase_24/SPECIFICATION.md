# Frozen benchmark and submission specification v1

## Problem and estimands

A declared bounded score is measured over a synthetic target population. The source supplies an anchor. A probability frame and a separate audit may cover different laws, even when both draw independently. Evaluate target mean coverage, threshold decisions, and certificates asserting source-anchor error ≤ .30. Width ≤ .60 defines precision. Decision threshold is .60. The threshold and width have different meanings. Case-level replicates are independent under the frozen generator. Rows inside a replicate are observations, and duplicate rows share an independent unit. Paired policies share the same case and replicate. The aggregate restricted stress contrast weights its four cases equally by design, without estimating prevalence.

Phase 18 uses a two-stratum law with a low tail rate .0002 and configured high rate and weight. Its scoring truth is .3 + 234.2 times the target tail rate. Conditional body and tail observations and the source rate are acquired separately. Phase 19 extension instead isolates jointly inaccessible mass m. With reachable rate r and hidden rate z, the target rate is (1−m)r+mz. A supplied cap U and unrestricted hidden support leave a width component 234.2U even with exact r. Invalid caps or hidden support may exclude truth. No variance or sample-size procedure can establish these identifying assumptions from the reachable channels.

## Input contract

The [archive catalog](../archive.json) is authoritative. Phase 18 config and archived raw cells contain seeds, sufficient counts and metadata. For a competing policy, use the acquisition export. It supplies a settings object and cases keyed by name. For each case:

| Field | Meaning |
|---|---|
| design.regime, weight, block, missing | Registered versus restricted access, nominal high-stratum weight, duplicate block size, missing-stratum flag |
| counts.source_tail | One source tail count per replicate. The frozen anchor is .3 + 234.2 times count/source_rows |
| counts.frame_units | Two independent-unit denominators for the frame |
| counts.frame_tail, audit_tail, audit_units | Two counts per replicate for each named stratum, with per-replicate audit denominators |
| counts.body_high, tail_high | Conditional body and tail counts, one per replicate |

Rows are indexed 0–511 within a case. Each method receives the complete package, with Phase 18 equal per-case purchase at the frozen tariff. Unit tariff is 133,120 per replicate. Verification tariff is 242,320 in registered and 233,320 in restricted cases. Standalone abstention buys nothing. Within the matched comparison its acquisition has already been charged. Pooling is allowed only for registered cases. The historical comparators are combined gate, audit-based direct, frame stratified, abstain and eligible pooling. A competing policy using extra information, a different purchase, different anchor or different tariff belongs to a different experiment. Phase 19's equal-spend and proxy-optimized allocations are separate designs and are reproduced but do not enter the Phase 18 submission track.

## Output contract

Submit UTF-8 CSV with the exact header below. Give one row per case and replicate in any order. Endpoints must be finite, ordered and inside [−240,240]. Certificate flag is `0` or `1`, independently of whether the interval determines a threshold call. Use [−240,240] and flag 0 for full fallback.

```csv
case,replicate,low,high,certificate
registered_matched,0,-240,240,0
```

Also provide implementation commit, executable commands, dependencies, package and CSV hashes, runtime and peak RSS, access declarations, failures, and a record of all development against published outcomes. A complete score requires 4,608 distinct rows. Missing, duplicate, unexpected or invalid rows fail the run. The scorer cannot verify what an entrant actually accessed or what it spent.

## Evaluation

Mean coverage includes both endpoints. Decide positive when low > .60 and nonpositive when high ≤ .60. Otherwise abstain. Count a certificate false when the raw source-anchor error exceeds .30. Compute all-run rates and Wilson 95% descriptive intervals. Conditional denominators are decisions or certificates as labeled. Zero denominators produce null estimates and intervals. Report widths, width quantiles, useful threshold decisions, false threshold labels, and unconditional false certificates separately. Utility is +1 for a correct certificate, −1 for a false certificate and 0 for no certificate. Use replicate-paired differences across the fixed four-case subset. The historical simultaneous Hoeffding comparison splits .05 across three comparators. Entrant comparison against combined is pointwise exploratory. No pass claim follows from it.

Use only allowed export fields and stated assumptions for predictions. Do not use latent target rates, benchmark outputs, case-name lookup rules or RNG seeds to select decisions. Case names are join keys. Published data cannot enforce this rule. A submission adapted to these outcomes must disclose that fact and remains exploratory. External entrants can retain their own code and consume the schema without modifying the frozen source or outputs.
