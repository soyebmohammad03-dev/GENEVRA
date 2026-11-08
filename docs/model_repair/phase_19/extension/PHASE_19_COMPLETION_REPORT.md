# GENEVRA Phase 19 extension

Coverage under incomplete sampling information · 8 November 2026

## Decision

**The coverage envelope recovered synthetic mean coverage when its external assumptions held. The allocation proxy failed the primary comparison.** This extension is a reproducible methodological feasibility result for GENEVRA. It establishes neither a new general statistical method nor journal readiness. The earlier Phase 19 publication audit is preserved as a separate historical artifact.

## Research question and development

Can externally justified bounds on the population missed by both streams support useful fixed-cost certification, and can a worst-case uncertainty proxy allocate samples efficiently when tail events concentrate in one stratum? Existing partial-identification results explain why shared blindness cannot be resolved internally. The gap tested here is how explicit bounds on inaccessible mass and hidden tail risk interact with GENEVRA's precision and acquisition decisions. [Manski](https://doi.org/10.1016/j.ijar.2004.10.006) · [Aronow and Lee](https://doi.org/10.1093/biomet/ass064) · [Tudball et al.](https://doi.org/10.1093/biomet/asac042)

The typed analysis module combines fixed-look Bernoulli KL bands and an exact rectangular mixture hull. It separates mean coverage, threshold decisions and anchor certificates. The planner searches the integer budget for the best Hoeffding width proxy. Its two-stratum cost is linear in the number of feasible allocations. The guarantee requires defensible external limits, correct reachable weights and independent latent draws. These limits and conditional score means are supplied in the benchmark. The module does not infer them from agreeing streams.

## Frozen experiment

Nine cases, two fixed budgets and 512 independent paired synthetic replicates per cell gave 9,216 replicates. The protocol froze before acquisition at 18:23:13 IST. At tariffs 1 and 2, equal spend and planned acquisition had the same total charge, with different latent denominators. The baselines were reachable-only, equal-spend envelope, and abstain-only. The full-hidden-support ablation removes one assumed restriction while retaining the mass cap. An exact reachable-rate oracle supplies a descriptive width floor. No hidden outcomes were sampled.

The score cutoffs remained .60 for the threshold and width, and .30 for allowable anchor error. The source anchor and conditional score means were fixed. This isolates the contribution of target coverage information, so these runs are not a rerun of Phase 18's distinct anchor and evaluation uncertainty.

## Results at the higher budget

| Case and outcome | Equal spend or reference | Planned envelope |
|---|---|---|
| Small omission, covered and precise | 450/512, median width .554 | 10/512, median width .667 |
| Large omission, mean coverage | Reachable only 0/512, 350 false certificates | 512/512, zero certificates |
| Valid hidden support, covered and precise | Unrestricted support 0/512, width 1.721 | 423/512, width .573 |
| Invalid mass cap, mean coverage | Equal envelope 0/512, 53 false certificates | 0/512, zero certificates |
| Invalid hidden support, mean coverage | Unrestricted support 512/512, zero certificates | 0/512, 101 false certificates |
| Eightfold duplicates, covered and precise | 0/512, width 1.448 | 0/512, width 1.758 |

The primary paired difference was **−.8594**, with a 95% Hoeffding interval of **[−.9794, −.7393]**. The prespecified superiority gate failed. At 32,768 units the planner assigned 25,378 outcomes to the low-event stratum and 3,695 to the high-event stratum. Equal spend assigned 16,384 and 8,192. The proxy favored the larger stratum and did not use the approximately 191-fold difference in tail probabilities. That undermined realized KL precision. No replacement allocation was tuned.

A .005 missing-mass cap with unrestricted hidden tail implies a width floor of 1.171 even with exact reachable rates. A valid hidden-tail restriction can lower that floor. A false restriction gives misleading precision. The observed invalid-support and invalid-cap cases demonstrate different failure modes. Neither justifies measuring real safety from these synthetic frequencies.

## Verification and cost

The benchmark ran in **0.39 seconds** at **39.9 MiB peak RSS** on Apple M3 using Python 3.12.15 and NumPy 2.5.4. The independent verifier reconstructed 18 cells, 90 method rows and 630 rates in **0.41 seconds** with a 1e-9 absolute tolerance. Integer outcomes and decisions agreed exactly. A fresh environment reproduced both raw and result files byte for byte using only the public baseline plus extension.

The full checkout suite passed **992 tests in 250.31 seconds**, with zero failures or skips and 94% coverage. The 12 focused tests also passed in the clean public-tree export. Ruff, strict mypy and evidence checks passed. The report, source, raw counts and outputs are separately preserved in the reproducibility artifact. Only synthetic sufficient counts were generated.

## Publication and external evidence

A negative feasibility paper is the strongest possible route. The result documents a useful distinction between controlling a worst-case proxy and actually getting precise decisions. It remains a synthetic stress test of established methods. A reviewer must challenge the equal-cost assumptions, adjudicate whether real external bounds can be supported, and test one independently specified comparator with actual acquisition and evidence costs. Confirmatory biological or simulator claims require separate held-out references. The manuscript foundation describes a conditional route, with submission still deferred.
