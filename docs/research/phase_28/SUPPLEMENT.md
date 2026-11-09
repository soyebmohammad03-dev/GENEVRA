# Supplementary methods and mathematical appendix

## Notation and scope

The [notation table](rendered/tables/notation.csv) accompanies Section 3 of the manuscript. The score is a bounded synthetic paired outcome. The Phase 18 generator has the form μ=(1−p)c+pt+qd, with residual mass q set to zero by the generator and retained in the analysis. Conditional means c and t are estimated from separate evaluations. The Phase 19/25 reduced law fixes c=.30 and t=234.50 and omits the residual component. These are distinct experiments and no scenario-level outcomes are pooled between them.

## Reachable and target bounds

For a stratum probability p, the Bernoulli log likelihood is k log(p)+(n−k)log(1−p), interpreted by its continuous limits at the boundaries. The production and reference implementations invert the fixed-look Chernoff threshold log(α/4) relative to the maximized log likelihood. The α/4 allocation splits total tail error over two strata and two tails. Weighting endpoints of the two intervals gives a simultaneous reachable-rate hull conditional on correct weights. In Phase 25, allocation may depend on the pilot. Conditioning on the independent pilot fixes the inference sample size, so the fixed-look argument applies under the frozen law.

Given r in [l,u], m in [0,U] and z in [0,V], monotonicity in r and z gives extremal targets (1−m)l and (1−m)u+mV. Their extrema over m occur at 0 or U. Thus the target tail hull is [(1−U)l, u+U max(V−u,0)]. At exact r with V=1, width in score units is 234.2U. This equality is an identification statement with supplied constraints, conditional on their truth. It does not attach confidence to estimated caps.

For each replicate define reachable score width W_R=234.2 Σ_h w_h(u_h−l_h) and envelope increment Δ=W_T−W_R, where W_T=H−L. In the reduced hull Δ=234.2 U[l+max(V−u,0)]. Arithmetic means preserve the decomposition. Useful precision is the replicate event 1{L≤θ≤H and W_T≤τ}. A threshold applied to an average width cannot recover the count of this event. Figure 4's stacked bars summarize means and mark the replicate cutoff for scale.

## Certification and error families

Phase 18 admission checks registry and frame/audit band disagreement. Its anchor error bound is distinct from the propagated target mean interval. Phase 25 certificates require the full target band to fit within the anchor tolerance. In both, unconditional false certification is the count of false issued certificates divided by all runs. Conditional false certification divides by issued certificates. If no certificates issue, the latter denominator is zero and conditional risk is undefined. Refusal and threshold abstention can differ.

For a paired difference D in [−M,M], Hoeffding gives radius M sqrt(2 log(2/α)/n). Phase 18 uses M=2, four equal restricted cases with 512 runs each, and α=.05/3 for three utility contrasts. For nine simultaneous one-sided safety bounds, invert the binomial lower tail at .05/9 per case. Phase 25 uses M=1, n=256, α=.05 for its primary cell, and α=.05/17 per other cell. The common inference prefixes pair policies within replicates. The frozen RNG design separates replicates. Pointwise Wilson summaries elsewhere do not replace these adjusted bounds.

## Frozen protocols and provenance

- Phase 18 frozen matched-access protocol is at `archive/phase-18/docs/model_repair/phase_18/MATCHED_ACCESS_PROTOCOL.md` after unpacking the [verified public capsule](../archive.json).
- [Phase 19 coverage-envelope protocol](../../model_repair/phase_19/extension/EXPERIMENT_PROTOCOL.md)
- [Phase 25 paid-pilot allocation and statistical plan](../phase_25/PROTOCOL.md)
- [Phase 26 separate exploratory sensitivity protocol](../phase_26/PROTOCOL.md)
- [Phase 27 reference reconstruction and external protocol](../phase_27/README.md)

The source-of-truth digest list is embedded in [evidence.json](rendered/evidence.json). Numerical text tokens are interpolated from that file's values during build. All result tables in the manuscript derive from the same extraction. The notation table is definitional. No new experimental outcomes were generated for Phase 28. Regeneration of existing synthetic experiments is part of the documented replay.

## Remaining scientific limits

No independently audited real target or measured frame-construction costs enter the reported experiments. Pilot, estimator, cap and interval choices were not evaluated on withheld laws. The Phase 26 sensitivity grid varies one factor at a time and does not estimate interactions or real prevalence. A field claim requires an approved and independently governed frame, reference, loss and cost protocol.
