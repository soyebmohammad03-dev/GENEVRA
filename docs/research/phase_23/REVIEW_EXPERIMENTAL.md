# Experimental design review

**Internally generated reviewer simulation. No independent peer review.**

**Recommendation.** Major revisions toward a reproducible benchmark and systems paper. The failure suite is reviewable now. Its baseline and reuse claims need stronger evidence.

## Major weaknesses and required revisions

1. **Audit comparability by regime.** Privileged direct access in Phase 16 and purchased-package matching in Phase 18 answer different questions. A standalone abstainer incurs zero acquisition expense, while abstaining after a matched purchase incurs the common cost. Publish per-comparison access and cost tables and avoid pooled ranks.
2. **Cost model and allocation objective.** Optimizing a Hoeffding proxy need not optimize a realized interval or usefulness. The equal-spend negative result is informative for the frozen costs. Compare against a prespecified variance-aware direct allocator, equal allocation and a fixed minimax rule using identical available metadata, target and all charged costs. Use a new registration if new observations are needed.
3. **Scenario representativeness.** A mixture of planted laws is a test suite. It is not deployment prevalence. Require a case-level failure table and a mapping from each case to an operational source of undercoverage. Show whether conclusions are sensitive to scenario weighting without choosing favorable weights.
4. **Independent artifact use.** Ask a researcher unfamiliar with the implementation to reconstruct results from the archived data and regenerate the figures. Ask for failure logs and checkers that avoid sharing the estimator implementation.

## Minor weaknesses

Mark which summaries are Monte Carlo estimates, deterministic sensitivity curves and paired contrasts. Distinguish immutable historical output from generated output. Explain exact versus numerically tolerant figure comparisons.
