# GENEVRA failure attribution

## Frozen Phase 25 reconstruction

Using the pinned raw digest, the audit recovered 4,608 paired synthetic replicates across 18 case-budget cells, 36,864 method records and all 18 contrasts. It regenerated stratum counts from the original seed namespaces, checked every allocation against exact spend and its policy objective, and recomputed interval endpoints using separate scalar likelihood inversion and closed-form envelope endpoints. Endpoints agreed within 8.21e−13 score units. Threshold classifications and counts agreed exactly. The primary difference was −103/256 = **−40.23 percentage points** with paired Hoeffding 95% interval **[−57.21, −23.26]**. There were 103 variance-only useful outcomes and zero proxy-only outcomes. All 17 Bonferroni-adjusted secondary intervals included zero.

## What explains the gap inside the benchmark

| Quantity at 32,768, small omission | Width proxy | Pilot variance | Equal spend |
|---|---:|---:|---:|
| Mean low / high stratum independent inference units | 25,080 / 3,652 | 21,887.82 / 5,248.09 | 16,192 / 8,096 |
| Mean weighted low-stratum width | .1165 | .1243 | .1454 |
| Mean weighted high-stratum width | .4393 | .3702 | .2953 |
| Mean envelope increment | .1168 | .1169 | .1169 |
| Mean final width | .6726 | .6113 | .5576 |
| Coverage | 256/256 | 256/256 | 256/256 |
| Coverage and width ≤ .60 | 1/256 | 104/256 | 229/256 |

**Demonstrated.** In this law the proxy moved draws away from the stratum whose weighted confidence band dominated width. The high-stratum term explains about .0692 of the .0613 net mean gap to operational variance. The narrower low-stratum term offsets part of that penalty. The omission-envelope increment is nearly identical. All these intervals covered, so the primary outcome gap came entirely from the width threshold. The maximum integer displacement of the proxy was .441 high-stratum unit from the continuous optimum across historical cells. Each reconstructed optimum matched its own mathematical objective. Rounding and an allocator implementation defect are unsupported explanations.

**Pilot effects.** The width proxy ignores pilot outcomes. A poor pilot cannot explain its allocation directly. The operational comparator's rare-stratum rate is noisy and its smoothing upwardly biases very rare probabilities. For a true rate .0002, expected smoothed rate is about .00407 with 128 trials. The historical oracle used 11,019 high-stratum draws and obtained 209/256 useful intervals, while the operational comparator averaged 5,248 and obtained 104/256. Equal spend still did better than the true-variance oracle on this endpoint. These observations support a distinction between optimizing sampling variance and optimizing a realized certification interval. They do not quantify a causal contribution of smoothing versus sampling error separately.

**Identification and costs.** With exact reachable rate, unrestricted hidden tail and valid mass cap U, width is at least 234.2U. The .005 cap in large omission gives 1.171, already above the .60 target. More reachable acquisition cannot eliminate it. With invalid caps, weights or support, narrower intervals can make coverage worse. The tariffs are synthetic per-row charges with duplicate blocks accounted for. Field frame acquisition, nonresponse management and cap construction were outside the cost model. A field cost ranking or a general claim about competing objectives remains untested.

## Exploratory interventions

Each cell below contains 96 common-seed runs. Counts are descriptive. The full machine-readable table also retains false certificates, threshold errors, abstention, utility, widths and oracle/direct diagnostics.

| Change | Width proxy useful | Variance useful | Equal spend useful |
|---|---:|---:|---:|
| Reference | 3 | 45 | 84 |
| Pilot 32 / 512 per stratum | 3 / 2 | 3 / 74 | 85 / 81 |
| Reported high-stratum pilot hits halved / doubled | 3 / 3 | 18 / 68 | 84 / 84 |
| Balanced / more imbalanced strata | 0 / 96 | 0 / 96 | 0 / 96 |
| Equal tariffs / high-stratum tariff 4 | 84 / 0 | 95 / 0 | 96 / 3 |
| Increased low / high stratum rate | 0 / 0 | 0 / 0 | 0 / 2 |
| No omission / large omission | 90 / 0 | 96 / 0 | 96 / 0 |
| Width limit .50 / .75 | 0 / 96 | 0 / 96 | 3 / 96 |
| Nominal 90% / 99% confidence | 27 / 0 | 79 / 3 | 95 / 17 |
| Budget 8,192 / 65,536 | 0 / 96 | 0 / 96 | 0 / 96 |

Changing pilot size jointly changes estimation noise and the inference budget. Distorting pilot counts at fixed cost isolates sensitivity of the plug-in allocation in this simulator. The invalid mass cap and low assumed high-stratum weight gave zero coverage for all three methods. With a high assumed weight, their coverage was 20/96, 4/96 and 2/96 respectively. The wrong hidden bound at the small reference omission still gave 96/96 coverage in all three methods because sampling bands could contain truth despite the invalid restriction. That does not validate the restriction. In the frozen Phase 25 large-omission invalid-support case both proxy and variance gave zero coverage. Observed coverage at one budget cannot establish an identification assumption.

The width-proxy deficit can disappear at a ceiling or floor, or under a smaller pilot that weakens the variance comparator. Neither those ties nor an advantage in a selected case demonstrate equivalence or general superiority. No rankings over untested interactions or deployment prevalence are warranted. See the [reconstruction](reconstruction.json) and [sensitivity results](sensitivity.json).
