# GENEVRA Phase 26 completion report

**Decision.** Preserve the width proxy as a negative comparator. The strongest current contribution is the reproducible benchmark of shared undercoverage, with diagnostic verification as supporting methodology. Journal submission, field recruitment and confirmatory validation remain on hold. No external reviewer, participant or partner was involved.

## Reconstruction and attribution

The audit regenerated and verified the frozen Phase 25 records, including all 36,864 method-replicate intervals, allocation objectives, stratum counts, costs and outcome classifications. It reconstructed 18 paired contrasts, including the multiplicity adjustment of 17 secondary contrasts. In the primary cell, width proxy minus paid-pilot Neyman was −40.23 percentage points, paired 95% interval [−57.21, −23.26]. All 103 discordant pairs favored Neyman. Equal spend had 229/256 covered-and-precise intervals, against 104/256 for Neyman and 1/256 for the proxy. All three had 256/256 coverage.

Within that synthetic law, the width proxy assigned fewer draws to the high-variance stratum. Its high-stratum interval term was .4393 against .3702 for Neyman. Their envelope increments were nearly identical. The exact optimization check ruled out integer rounding as the source of the allocation gap. Pilot noise and smoothing constrain the operational variance policy, and the oracle's lower variance did not guarantee the most useful intervals. The audit does not infer a universal method ranking or isolate field costs.

## Separate sensitivity sweep

The separate frozen design used 23 scenarios and 96 common-seed replicates per scenario. Pilot size and distortion altered operational variance performance. Stratum balance, tariffs, prevalence, width threshold, nominal confidence and budget produced floor and ceiling effects. Invalid weights and the bad mass cap could destroy coverage, while some invalid hidden support remained undetected at small omission. The historical large-omission invalid-support case still fails. The [failure attribution](FINDINGS.md) records the observed counts and scope. The sweep is exploratory and contains no held-out or field evaluation.

## Verification and preservation

On macOS 27.0.1 arm64 with 8 GiB RAM and the pinned CPython 3.12.15 / NumPy 2.5.4 environment, the clean audit took 13.53 seconds after Phase 25 regeneration and used maximum RSS 104,775,680 bytes. The reconstruction and sensitivity JSON files matched the initial execution byte for byte. Independently calculated endpoints differed by at most 8.21e−13 score units. The historical challenge verified all ten entries and all three primary figures in 132.91 seconds with maximum RSS 388,333,568 bytes. Its verification matched the Phase 24 public replay on every non-timing field.

The full suite passed 1,068 tests in 251.72 seconds, including 11 new tests, with no failures or skips and 94% reported coverage. Peak RSS was 241,958,912 bytes. Ruff lint and formatting, strict mypy in its configured source scope and evidence verification passed.

All 18,143 inventoried historical SHA-256 entries matched and all 29 historical ZIPs passed CRC. Every tracked parent file besides the root README remained byte-identical. The README only gained the Phase 26 link. The audit runner, tests, protocol, documentation, checked JSON and manifest are new. Existing uncommitted work was preserved.

## Readiness

The [manuscript foundation](MANUSCRIPT.md) leads with the negative result and defines the narrow benchmark contribution. The [publication positioning](POSITIONING.md) favors a benchmark and systems paper, with a scoped negative feasibility report as fallback. A new methods paper is unsupported. Independent replay, a nearest-benchmark comparison, and a withheld synthetic test with locked policies are the next technical evidence. Empirical inference additionally needs an independently governed and audited target frame, measurements, realistic costs and approvals. The [review checklist](REVIEW_CHECKLIST.md) is ready for an external statistician.
