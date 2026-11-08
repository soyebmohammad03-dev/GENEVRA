# Internal adversarial statistical review

This is an internal assessment written from a statistician's perspective. It records no outside review or endorsement.

| Challenge | Assessment and disposition |
|---|---|
| Target estimand vs observed frame | The estimand is the full synthetic mean. Independence of draws from two frames cannot establish union coverage. The planted example supports a possibility claim, not a real prevalence claim. |
| Missingness and external constraints | The exact reachable-rate floor follows from the rectangular bound set. It relies on the declared cap and support. The wrong-cap and wrong-weight cases show that precision under a misspecified set is uninformative about coverage. No data-driven cap estimator has been validated. |
| Certificate correctness | Phase 18 certifies with a nuisance error bound and admission. Phase 25 uses interval containment. 180/512 is the unconditional event count. 180/180 among issued is descriptive, and the 40.73% bound cannot be interpreted as conditional safety. |
| Fair comparison and costs | All paid arms consume the same synthetic pilot and charged budget. That includes fixed policies that could skip the pilot in another design. The oracle sees latent rates and refusal buys no observations. Real frame, lab, staff and nonresponse costs were not measured. |
| Paired analysis and power | Policies share prefixes within replicate, with independent synthetic replicate streams. Hoeffding intervals control the declared bounded contrasts and can be conservative. Null-containing secondary intervals do not resolve small effects or establish equivalence. Equal spend comparisons are descriptive. |
| Multiplicity and selection | Phase 18 has three utility contrasts and nine simultaneous safety bounds. Phase 25 uses a primary contrast and separate 17-case family. The public frozen cases are not held out. The sensitivity sweep does not support confirmatory ranking. |
| Width attribution | The final verifier recomputes weighted widths and the envelope increment from raw counts before averaging. A mean-width threshold is invalid for classifying single runs. Identical coverage in the primary case isolates the width criterion. It does not prove universal variance-allocation advantage. |
| Generalizability | These deliberately bounded cases illustrate mechanisms. No external use, distinct deployment prevalence, estimated weight error model or independently measured target outcomes are established. |

## Evidence categories

- **Demonstrated synthetic findings.** Shared blindness, cap-dependent recovery, the negative primary allocation contrast and its width decomposition.
- **Established statistical theory.** Partial identification, stratified variance allocation, fixed-look concentration, exact binomial inversion and paired bounded-difference intervals.
- **Engineering contributions.** Frozen known-truth inputs, tariff controls, independently written calculation code, reproducible tables, figures and release.
- **Plausible interpretations.** Separate measures can help an auditor distinguish poor allocation from invalid access. The comparative advantage of this package over the closest software awaits independent use.
- **Unverified real-world implications.** Field safety, coverage, costs and benefit. Independent frames and outcome adjudication would be required.

**Decision.** Circulate for independent technical assessment. Keep journal submission on hold. Preserve the failed allocator as a comparator. No further engineering phase is planned.
