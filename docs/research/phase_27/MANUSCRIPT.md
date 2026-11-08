# GENEVRA: A reproducible benchmark for certification under shared sampling-frame undercoverage

## Abstract

Calibration and evaluation samples can agree while jointly omitting target units. We present GENEVRA, a frozen known-truth benchmark and separate numerical reference implementation for distinguishing target coverage, useful precision, anchor certification and acquisition cost. In a shared-blindness stress case, zero of 512 intervals covered the target mean and all 180 issued certificates were false, although no threshold label was wrong. In the prespecified small-omission comparison at matched synthetic cost, a GENEVRA width proxy yielded 1 of 256 covered-and-precise intervals, compared with 104 for paid-pilot cost-adjusted Neyman and 229 for equal spend. The paired difference versus Neyman was −40.23 percentage points (95% Hoeffding interval −57.21 to −23.26). Valid omission bounds restored coverage in a separate case without achieving useful precision. The artifact preserves these negative results and provides public counts, frozen budgets and independently implemented checks. Its claims concern declared synthetic laws. External reproduction, empirical validation and evidence of broader usefulness remain outstanding.

## Introduction and motivation

A sampling channel can draw many independent observations from the wrong population. A second independent channel may fail to detect the difference if both use similarly incomplete frames. In that situation observed agreement is evidence about the reachable population. Operationally it can still trigger an erroneous certificate about the target. GENEVRA asks whether an evaluation can expose this error while distinguishing identification restrictions, sampling variability and decision costs.

## Related work and gap

Missing-data bounds and interval identification explain why unobserved outcomes matter. Multiple-frame survey methods characterize when overlap and independent probability designs improve coverage. Nonresponse diagnostics quantify disparities under observed auxiliary variables. Selective prediction and risk calibration show why issuance and error should be reported separately. Cost-constrained allocation and simulation design are established. The closest inferential software, `selectioninterval`, addresses estimated restrictions under a different target and model. OpenML imputation benchmarks test cell reconstruction and downstream prediction. Neither is a direct comparator on a missing population domain with anchor decisions. The closest field analogue is an independent spatial survey that exposed omissions in alternative Norwegian fisheries frames. These overlaps narrow the claim to the particular benchmark and its verification package. See the [comparison matrix](NOVELTY.md).

## Research questions and contribution

1. When can correlated frame omission produce false certificates despite observed agreement?
2. When do independent omission bounds improve target coverage, and what precision remains attainable?
3. At identical synthetic acquisition budgets, how does allocation change useful precision and certification?
4. Can a separate implementation reproduce the decisions, budgets and intervals from underlying records?

The contribution is the combination of versioned cases, explicit information and cost controls, negative findings and a public verification path. The code implements established statistical methods. It provides a benchmark for independently comparing operational policies under these assumptions.

## Mathematical foundations

For reachable tail rate r, omitted fraction m and hidden tail rate z, target rate is (1−m)r+mz. Apply the score transformation .3+234.2 times the rate. With known reachable rate and unrestricted hidden support, the width induced by an admissible cap U is 234.2U. More draws from reachable strata reduce sampling error only. The procedure uses stratified fixed-look likelihood bounds and propagates their endpoints through the partial-identification hull. Calibration source anchors, .60 threshold decisions, .60 width and .30 anchor tolerance define separate outputs. A certificate may be wrong even when the threshold label is correct.

## Benchmark design and protocol

Phase 18 contrasts registered and restricted frame access, shared blindness, asymmetric stale streams and missing strata. Phase 25 uses nine frozen laws at two budgets with frozen tariffs, with 256 paired synthetic replicates per case-budget cell. All paid policies see a common 128-per-stratum pilot, then buy independent inference samples with common prefixes. Compare the proxy, paid-pilot cost-adjusted Neyman, minimax variance, proportional units and equal spend under the same envelope. Include direct reachable calibration as an assumption-violation diagnostic, a true-rate oracle as privileged and no-acquisition abstention separately. The primary paired Hoeffding interval concerns small omission at 32,768 charged units. Seventeen secondary contrasts share a separate Bonferroni family. Phase 26 sensitivities remain exploratory. Phase 27 introduces no new scenario outcomes. See the [design and comparator ledger](DESIGN_AND_COMPARATORS.md).

## Results and negative findings

The width proxy lost the prespecified primary comparison. All 103 discordant pairs favored pilot variance. The corresponding counts were 1/256 and 104/256, with 229/256 under equal spend. Coverage was 256/256 for all three, so the gap concerned width. All adjusted secondary intervals included zero. In the Phase 18 shared-blindness case all 180 issued certificates were false. The simultaneous upper bound on unconditional false certification was .4073. There were zero mean coverage successes and zero wrong threshold calls. In the Phase 19 large-omission case a valid supplied cap restored coverage in 512/512 while useful precision remained zero.

## Sensitivity and failure attribution

The primary proxy spent fewer observations on the high-variance stratum. This stratum's mean weighted interval width was .4393 versus .3702 for pilot Neyman. The envelope increments were nearly equal and integer rounding displaced the optimum by less than a high-stratum draw. Pilot error changes the operational variance rule and neither allocation objective ensures useful precision. The exploratory sweep found floor and ceiling effects at different budgets and precision cutoffs. Incorrect weights and cap restrictions could destroy coverage. These interventions explain local benchmark behavior and do not estimate field prevalence.

## Reproducibility and threats

The public script installs a pinned environment, checks archived digests, regenerates figures, recreates Phase 25 counts and runs a separate reference implementation. That implementation rebuilds every Phase 25 interval from counts and scores Phase 18 from verified endpoint/certificate arrays and raw anchor counts. Archived Phase 18 code separately reconstructs the upstream arrays. The new reference shares specifications and data and uses no GENEVRA analysis functions. Project members ran it internally. Configurations and outcomes are public, and a new seed would not create a holdout. The benchmark uses stipulated prices, nominal weights and supplied restrictions. Field acquisition costs, genuine frame audits, conditional safety and participant outcomes are unavailable. No empirical or biological claims follow.

## Discussion and conclusion

The failed allocation rule remains scientifically useful as a counterexample to treating optimizer correctness as outcome superiority. The strongest candidate paper is a combined benchmark and verification artifact. The next evidence is an external reconstruction and comparison with the closest available artifact, followed by a separately governed withheld evaluation for any transfer claim. A narrower negative feasibility report is a fallback. Journal submission and empirical validation remain on hold. See the [external protocol](EXTERNAL_PROTOCOL.md).
