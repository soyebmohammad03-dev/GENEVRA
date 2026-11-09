# Phase 25 findings and contribution matrix

The prespecified primary public-scenario result is a difference of **−0.40234** in covered-and-precise probability for the GENEVRA width proxy minus operational variance-aware allocation, with paired 95% Hoeffding interval **[−0.57211, −0.23258]**. The advantage criterion failed. Equal spend performed better descriptively than both in this case. The oracle is informative about the variance objective and has privileged information. At the primary budget, the median width was .672 for the width proxy, .610 for operational variance, and .559 for equal spending. The low-rate stratum recorded zero pilot hits in 253 of 256 replicates. Smoothing and the difference between the variance and useful-precision objectives limit the operational comparator.

## Selected contrasts at 32,768 charged units

Each denominator is 256. See [all 144 cells](results.json), [all 18 paired contrasts](contrasts.csv) and the [contrast figure](allocation.svg).

| Case | Width proxy useful | Variance useful | Equal spend useful | Interpretation |
|---|---:|---:|---:|---|
| Complete | 241 | 251 | 256 | Direct and equal spend coincide with zero omission cap |
| Small omission | 1 | 104 | 229 | Width proxy loses to operational variance in primary contrast. Direct had 256 here but assumes away omission |
| Large omission | 0 | 0 | 0 | All three covered 256. Direct covered zero and issued 189 false certificates |
| Shifted reachable | 0 | 1 | 8 | Reachable-only direct had 216 useful intervals in this particular cell. Its identifying assumption is violated |
| Near threshold | 256 | 251 | 256 | Width proxy has a small descriptive lead over variance, with adjusted interval crossing zero |
| Verified hidden support | 211 | 247 | 256 | Nominal support information is valid. Width proxy yields fewer useful intervals descriptively |
| Bad mass cap | 0 | 0 | 0 | Both allocations had zero coverage. Variance issued 12 false certificates versus zero for width proxy |
| Bad hidden support | 0 | 0 | 0 | Both had zero coverage. Width proxy issued 42 false certificates versus 113 for variance |
| Duplicates | 0 | 0 | 0 | Coverage without useful precision. Both pay for duplicated rows while using only independent counts |

All 17 adjusted secondary intervals include zero. At 8,192 neither of the two primary methods recorded a covered-and-precise interval in any case. In the large-omission case with a valid cap, the width floor alone exceeds the useful width. In invalid cap/support cases, abstention avoids false certification but yields no precision, and its zero acquisition cost belongs to a separate refusal comparison. Reduced certification from wider intervals does not rescue mean coverage.

## Contribution and publication gate

| Claim | Disposition |
|---|---|
| GENEVRA's width proxy is superior under equal acquisition cost | The primary public synthetic case shows the opposite for the prespecified endpoint |
| Variance-aware allocation is generally optimal for useful certification | Unsupported. It optimizes plug-in variance and can lose to equal spending or issue more false certificates under invalid assumptions |
| A valid external envelope can restore coverage where direct reachable inference fails | Reproduced conditionally under the declared synthetic law, often without useful precision |
| One can benchmark allocation, identification and refusal separately | Strengthened by the executable paid-pilot comparison, common-prefix design, and separately checked costs and scoring |
| A new statistical method or empirical operating claim | Unsupported. Established allocation and partial-identification methods are integrated into a stress benchmark |

Phase 18 shared-blindness, missing strata and asymmetric staleness remain in the separate historical replay. The Phase 19 allocation suite assumes both reachable strata are available and holds their weights fixed. No allocation effect is inferred for missing strata or unknown weights.

The benchmark and systems route remains the strongest submission candidate after independent reproduction and review. Journal submission, recruitment and empirical validation remain on hold. There is no independent synthetic holdout and no representative deployment distribution. The study does not measure field frame construction, external cap, anchor or measurement costs, and does not compare alternative pilot sizes or a fixed policy that can skip the pilot. Integer optimality is for estimated variance only. No additional conditional body/tail evaluations are bought because the score means are fixed and shared.
