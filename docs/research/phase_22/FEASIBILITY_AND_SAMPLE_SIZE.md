# Feasibility and sample-size analysis

## What 12 episodes can establish

**Current disposition is NO-GO for recruitment.** There is no committed partner, operational roster, separately governed area audit, lab reference or cost ceiling. A 12-episode pilot is feasible in principle only after those prerequisites and field authorization. It can demonstrate whether these specific crews and systems can enumerate, reach omitted strata, collect blinded reference samples, adjudicate, reconcile invoices and release approved aggregates. It cannot establish safety, superiority, general enumeration completeness or field transport.

Use the gates below as proposed operational criteria. Register all thresholds, assay, counts and cost ceilings before collection. These gates screen feasibility and do not estimate population pass rates.

| Gate | Required observation |
|---|---|
| Prelaunch | Named independent roles and signed access/release terms, enumerated provisional roster, feasible probability area audit, assay QC limits, cost ceiling, and a route to sample the neither-channel stratum |
| Enumeration and provenance | All 12 episodes have a frozen roster, independent area-audit plan, positive reference probability in every eligible stratum, documented duplicate and overlap decisions, and reproducible seed/draw |
| Off-channel access | Independently observe eligible off-channel units and complete at least one reference measurement in that stratum in at least two episodes. If the proposed setting has no evidenced shared omission, it cannot test that failure mode |
| Adjudication | At least 10 of 12 whole-episode reference bands have width ≤min(w/2, delta/2), with the joint reference error allocation and all unresolved units retained |
| Costs and governance | Every episode has paired identical acquisition-package hashes, reconciled ledgers, locked decisions before reference release, and no unresolved material blinding, permission or release deviation |

Do not substitute a new episode after adverse outcomes. A safety or permission stop takes precedence over completion. Report all incomplete attempts. Reassess design if any gate fails. An operational pass only licenses a separately powered review and registration.

## Fixed-sample calculations

Use alpha=.02 for each directional primary gate. For observed adverse count k in n independent episodes, invert P_p(X≤k)=.02 for the exact upper limit. With zero adverse events in 12 episodes the upper limit is **27.82%**. Zero events would occur about **54.0%** of the time at true 5% adverse risk. All 12 successes on an independent binary feasibility indicator give a one-sided 98% lower bound of only **72.18%**. The most favorable pilot outcome cannot pass the 5% safety gate. The paired one-sided Hoeffding radius for a difference in [-1,1] is **0.8075** at n=12.

For each fixed n, set k_max to the greatest k with Bin(n,.05) lower-tail probability ≤.02. Power at true adverse risk p is P_p(X≤k_max). No count passes when k_max=-1. At n=77 only zero can pass; at n=209 at most four can pass. The exact grid for risks .005, .01, .025, .04, .05 and seven sample sizes is in [design_receipt.json](design_receipt.json). The event rate includes unresolved issued calls, so pilot adjudication failures can make effective risk much higher than the assumed latent false rate. Report issuance and conditional risk separately. A zero-event threshold of 77 is a best-case bound, not a recruitment plan.

For useful gain use the paired mean minus sqrt(2 log(1/.02)/n). An observed +.20 would need at least 783 independent episodes to clear a +.10 margin. For a true +.20, a sufficient bound for 90% power is n≥(sqrt(2 log 50)+sqrt(2 log 10))²/.10², or **2,444 episodes**. That is a conservative sufficient size, not an estimate of what a partner must recruit. Use a preregistered exact paired or cluster-valid design if pilot evidence supports a less conservative plan. Do not choose among methods after unblinding.

## Precision, dependence and unresolved data

Reference precision and policy coverage are separate. Choose reference sample counts by exact hypergeometric inversion for each candidate roster size and expected count, using the joint allocation and a grid of label completions. Recompute after adding the missing-frame hull. If the width floor from a valid off-frame cap exceeds the reference threshold, larger on-frame samples cannot solve the problem. Under independent episodes the worst-case standard error of a coverage proportion is 0.5/sqrt(n). This is roughly .144 at 12 and .035 at 209. Illustrative two-sided normal widths are about .57 and .14 at worst variance; use exact limits for inference, particularly near 0 or 1. Plan with both near-nominal and lower coverage, not observed simulator coverage.

For planning only, variance inflation with equal cluster size b and ICC rho is 1+(b−1)rho. Combine with an independently projected operational loss l using ceil(n times inflation divided by (1−l)). The receipt compares b=1 to three clustered regimes. These counts do not validate binomial or Hoeffding bounds under dependence. If watersheds or crews induce clustering, design and analyze at the defensible independent cluster level, or use the actual finite-population design. An eligible unresolved label is not an excluded record. Loss inflation is a budgeting sensitivity for irrecoverably lost episodes, while the primary safety analysis treats unresolved issued decisions adversely. Register how episodes lost before any decision enter the denominators and conduct worst-case sensitivity. No optional efficacy stopping. Restart or redesign before outcomes if the reference frame, assay or independence assumptions fail.

Methods references: [Clopper and Pearson, Biometrika 1934](https://doi.org/10.1093/biomet/26.4.404), [Hoeffding, JASA 1963](https://doi.org/10.1080/01621459.1963.10500830), and the [EPA NRSA design and QA document](https://www.epa.gov/system/files/documents/2024-12/nrsa-2018-19-tsd-final-11252024.pdf).

| Independent episodes | Maximum passing events | Power if risk is 1% | Power if risk is 2.5% | Power if risk is 4% |
|---:|---:|---:|---:|---:|
| 12 | None | 0% | 0% | 0% |
| 77 | 0 | 46.1% | 14.2% | 4.3% |
| 209 | 4 | 94.0% | 39.9% | 7.7% |
| 500 | 15 | 100.0% rounded | 80.9% | 15.1% |
| 783 | 26 | 100.0% rounded | 93.8% | 19.1% |

At a planned 209 independent units, the variance-only budgeting sensitivity yields 256 nominal units at cluster size 3, ICC .05 and 10% loss; 418 at size 4, ICC .20 and 20% loss; and 654 at size 6, ICC .30 and 20% loss. A real cluster design also needs enough independent clusters. No clustering or loss assumption in this grid is empirically established.
