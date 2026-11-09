# GENEVRA benchmark design and comparator validation

## Target and inference

The allocation task estimates a bounded score mean from two reachable Bernoulli strata. Let r be the known-weight mixture of the stratum rates, m the omitted target fraction and z its hidden tail rate. Target tail rate is (1−m)r+mz, then score is .3+234.2 times that rate. With reachable interval [L,H], supplied m≤U and z≤V, the probability hull is [(1−U)L, H+U max(V−H,0)]. If r is known and V=1, width is U before score conversion. An invalid cap can exclude the true target even with unlimited reachable observations.

Phase 25 uses the same alpha-split fixed-look likelihood inversion per sampled stratum. For k successes in n trials retain the set where log likelihood relative to its maximum is at least log(alpha/4), then weight both endpoints. Separate independent pilot and inference stages preserve conditional sampling validity for adaptive allocations. Exact row charges include duplicate blocks but only independent-unit counts enter inference. Certification requires the entire score interval to lie within .30 of the anchor. A threshold label uses .60. Precision requires width ≤ .60. These thresholds play distinct roles.

## Information and cost ledger

All paid Phase 25 arms know nominal weights, two stratum definitions, tariffs, the common paid pilot and a fixed inference budget. Eligible envelope methods receive the same exogenous cap and hidden-support constraints. These inputs are assumed provided at common cost outside the synthetic tariff. After acquisition, only their selected independent inference counts enter the estimator. The evaluator has latent truth. All matched arms pay exactly the same charge. Fixed rules could skip a pilot in deployment, a separate comparison from this intervention.

| Comparator | Allocation and estimator | Privilege, boundary and expected failure |
|---|---|---|
| Width proxy | Integer optimum of sum(weight/sqrt(n)). Weighted likelihood envelope | Ignores pilot and actual stratum variance. Correct optimizer can underperform for realized useful width |
| Equal spend | Equal cost in each stratum. Same weighted envelope | No privileged variance information. Counts differ under unequal tariffs |
| Proportional units | Nearly proportional integer allocation under the exact tariff. Same envelope | Depends on nominal weights. No optimization guarantee |
| Pilot cost-adjusted Neyman | Minimize sum(weight² × smoothed pilot variance/n). Same envelope | Uses available pilot counts, with separate inference. May overestimate very rare rates and optimize a different loss from useful precision |
| Minimax variance | Use worst-case Bernoulli variances .25 and the same exact budget. Same envelope | Conservative for worst-case sampling variance. Cannot fix target identification |
| Direct reachable calibration | Equal-spend data and likelihood interval without omission expansion | Identifies full target under complete access or an independently justified equivalent law. Diagnostic under missingness |
| True-rate variance oracle | Cost-adjusted Neyman using latent stratum rates | Explicit privileged information. Diagnostic only |
| Always abstain | No purchase. Full physical range and no certificate | A refusal control with a different cost. Useful precision is zero |

Literal equal independent counts cannot exhaust every original tariff budget with the required integer counts. Equal spend is the natural fixed comparison. Classical Neyman is the equal-cost limit of the cost-adjusted variance objective and is addressed in the Phase 26 equal-tariff sensitivity. No new rankings were run. The Phase 18 direct baseline uses an audit stream within its separate matched package, so its acquisition costs and information do not transfer to Phase 25.

Exact Clopper–Pearson stratum intervals could substitute for likelihood concentration if compared under the same fixed design and error allocation. Wilson intervals describe Monte Carlo rates in the historical tables and are not full-target bounds. An asymptotic partial-identification interval changes assumptions on estimated restrictions. Confidence sequences address optional looks, which are absent here. The existing baselines suffice to diagnose the stated failure and objective mismatch. A journal claim about general efficiency would need a separately frozen comparison of interval choices and paid acquisition under realistic cost and access, plus a withheld benchmark. See the [closest-work audit](NOVELTY.md).

## What the scenarios can and cannot represent

| Boundary | Exercised evidence | Unresolved |
|---|---|---|
| Shared vs asymmetric errors | Phase 18 shared blindness, frame-only staleness and audit-only staleness distinguish draw independence from common frame omission | No calibrated correlation gradient, dynamic correlated nonresponse or operational prevalence |
| Missing strata and nonresponse | Phase 18 missing-stratum stress leads to refusal. Phase 22 proposes separate disposition accounting | Frozen case conflates loss of support and nonresponse. No response mechanism or field adjudication identified |
| Wrong weights and rare populations | Phase 15 wrong weights, Phase 19 rare tails and Phase 26 weight and prevalence sensitivities | Estimated weights, coverage-error uncertainty and adaptive frame acquisition absent |
| Hidden support and invalid external evidence | Phase 19 valid/invalid mass and hidden-tail caps, Phase 26 width-floor analysis | No independent field cap or hidden-support measurement |
| Unequal cost and duplicates | Phase 25 matched tariffs, explicit block charges, common pilot and distinct oracle | Real costing, frame construction and workflow time remain unknown |
| Coverage, width and risk | Complete, small and large omission, threshold and refusal cases distinguish endpoints | No prevalence-weighted deployment utility or conditional safety validation |

Synthetic runs are independent replicates under declared laws. Independent random draws can still sample identically incomplete frames. Two channels that miss complementary domains may restore target access only if their union covers the target and overlap can be measured. GENEVRA tests contrasting mechanisms but does not estimate that condition in a real population.
