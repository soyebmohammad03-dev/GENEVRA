# Phase 25 completion report

**The width proxy lost the prespecified primary synthetic comparison.** The benchmark is ready for external technical challenge. Journal submission, recruitment and empirical validation remain on hold. No partner or external participant was contacted, and no confirmatory campaign ran.

## Design and outcome

Phase 25 froze a separate comparison before executing 256 paired runs for each of the nine Phase 19 laws at each of two budgets. Each matched policy received and paid for 128 independent pilot draws per stratum and used an independent inference stage. The competing allocations were cost-adjusted pilot-estimated Neyman, GENEVRA's width proxy, minimax variance, equal spend and proportional independent units. A direct reachable calibration arm shared the equal-spend acquisition. The true-rate variance oracle and the zero-acquisition abstention control were reported separately. Frame and external cap acquisition were outside the synthetic costing model. No assumption of field cost equality follows.

At 32,768 charged units in the small-omission case, the width proxy yielded 1/256 covered-and-precise intervals, operational variance yielded 104/256, and equal spend yielded 229/256. The prespecified contrast was −40.23 percentage points, with 95% paired Hoeffding interval [−57.21, −23.26] points. All 17 adjusted secondary intervals included zero. The width proxy's near-threshold result of 256/256 versus 251/256 for variance is descriptive. It issued fewer false certificates under bad hidden support (42 versus 113), but neither method covered the target. See the [results and failure analysis](FINDINGS.md).

## Engineering and verification

The runner checks the Phase 19 and Phase 25 protocol/configuration digests, validates paid allocations, shares prefix draws across policies, and emits a raw CSV, summary, contrast table, figures and receipt. The separate verifier checked all 36,864 method-replicate records, 144 cells and 18 contrasts. It checks nested counts and recomputes interval endpoints and objective minima on the fixed audit subset. The supplied proportional entrant was run and checked as an interface fixture. These are internal checks.

- Fresh pinned comparison environment on MacBook Air M3 with 8 GiB RAM, macOS 27.0.1 arm64, CPython 3.12.15, NumPy 2.5.4 and uv 0.12.23. Clean comparative replay took 9.43 s with maximum RSS 93,372,416 bytes. The raw CSV, contrasts and SVG use normalized text endings. The scientific results JSON remained byte-identical to the initial run.
- Ten historical replay entries and three figures passed. The Phase 24 verification receipt matched on all non-timing fields. Historical replay took 131.60 s with maximum RSS 405,487,616 bytes.
- All 18,143 inventoried historical hashes and 29 archive CRCs passed. The public parent had 443 tracked files. Its only edited path is the root README, which adds the Phase 25 link. Earlier worktree changes were preserved.

- Full working-tree suite passed 1,057 tests in 245.93 s, including 24 new comparator tests, with no failures or skips, 94% reported coverage and maximum RSS 235,405,312 bytes. Ruff lint and formatting, strict mypy for the configured source scope and committed evidence verification passed.

## Scientific decision

The comparative result strengthens the benchmark contribution and weakens any claim for the allocation proxy. The primary difference is interpretable within the specified synthetic case and cost package. The public cases cannot confirm general superiority, and different weights, a larger pilot, sequential reuse or unequal frame costs require separate designs. The next prospective gate is an externally governed held-out comparison with locked policies, independent scenario selection and fixed loss and cost rules. Empirical validation also needs an independent reference frame, approved access, and measurements. See the [reproduction and entrant instructions](REPRODUCE.md).
