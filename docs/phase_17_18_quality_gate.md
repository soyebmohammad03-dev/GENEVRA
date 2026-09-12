# Phase 17/18 Scientific Quality Gate

Honest answers to the spec's 17 required questions, following the same
convention as `docs/phase_15_16_quality_gate.md`.

**1. Can GENEVRA now run multi-seed research campaigns reliably?**
Yes, at the scale actually validated: `CampaignRunner` executed a real
2-condition x 4-replicate campaign end to end, with every cell's raw
result preserved on disk. Not validated at `STANDARD`/`RESEARCH` mode
sizes — only `PILOT`-scale smoke tests were run.

**2. Can campaigns resume after interruption?**
Yes, demonstrated directly: a checkpoint cell was manually forced into
`RUNNING` (simulating a killed process), reloading the checkpoint
reclassified it `INTERRUPTED`, and a subsequent `campaign-resume` call
redid only that one cell while leaving the other 7 completed cells
untouched (see the live-validation section of the final report).

**3. Are independent seeds genuinely independent?**
Yes for the seed *derivation*: built on `numpy.random.SeedSequence.spawn`,
tested for determinism, cross-condition distinctness, and prefix-stability.
Whether the resulting simulation trajectories are statistically
independent depends on `ContinuousEvolutionEngine`'s own RNG usage
downstream of the seed, which this phase did not re-audit (it was already
GENEVRA's existing reproducibility contract from Phase 1-2).

**4. Is pseudoreplication prevented?**
By construction in the campaign layer: `AnalysisPlan.replication_unit`
is hard-validated to equal `"seed"` (raises otherwise), and
`condition_values`/`summarize_replication_consistency` only ever operate
on one value per replicate, never per-organism data.

**5. Are confirmatory and exploratory analyses separated?**
Yes: `build_multiple_comparison_registry` labels every record from
`benjamini_hochberg`'s existing `is_primary` mechanism, and
`CampaignReport` keeps `confirmatory_findings`/`exploratory_findings` as
separate fields with an explicit caution note distinguishing them.

**6. Is multiple testing handled?**
Yes, by reusing `genevra.discovery.multiple_testing.benjamini_hochberg`
(no second correction procedure implemented) — every p-value examined in
a campaign is corrected together as one family.

**7. Can current metrics predict future evolutionary outcomes
out-of-sample?**
Not established by this phase. `leave_one_seed_out`/`within_seed_holdout`
(Phase 16) are the machinery; Phase 17/18 did not run a new large-scale
predictive study, only exercised the existing machinery and added
explicit leakage tests proving it does not cheat.

**8. Is temporal leakage prevented?**
Yes, and now with direct tests, not just inspection: one test constructs
data where leaking a held-out seed into training would flip the predicted
sign, and confirms the real `leave_one_seed_out` does NOT flip (while
demonstrating what a leaky pooled fit WOULD look like, for contrast);
another confirms `within_seed_holdout`'s train fit is byte-identical
whether or not the held-out segment is later mutated.

**9. Can GENEVRA reproduce literature-inspired qualitative patterns?**
Inconclusive at the scale tested here. The live boundary-search and
literature-campaign runs (CASE A, pop=8-10, generations=6-8, 4-6 seeds)
all returned `INCONCLUSIVE` — no distinguishable effect at this sample
size. This is reported as the actual finding, not adjusted or hidden.
Phase 11's own larger-scale runs (pop=16, generations=20, 8 seeds) may
behave differently; re-running the same cases at that scale was not done
in this session.

**10. Can GENEVRA identify meaningful boundary conditions?**
The machinery exists and ran on real data (`run_boundary_sweep` over
CASE A's `period` at 3 values); the specific live run found zero label
transitions (every value stayed `INCONCLUSIVE`) — an honest "no boundary
found at this scale," not a discovered boundary.

**11. Can it distinguish alternative explanations experimentally?**
`rank_falsification_experiments` orders the confound hypotheses
Phase 11.5 already generates, but this phase did not run a discriminating
experiment against a confound and observe its outcome — only the ranking
step is new and validated; actually distinguishing explanations still
requires executing the top-ranked proposed experiment, which was not done.

**12. Is literature mismatch explicitly represented?**
Yes: `ComparisonRow.to_dict()["model_mismatch"]` surfaces
`claim.known_limitations` directly into the comparison matrix; nothing new
is asserted about mismatch beyond what Phase 11's cases already documented.

**13. Is every result traceable to raw experiment data?**
For campaigns: yes (this phase's core deliverable — see
`docs/research_campaigns.md`). For the standalone `boundary-search`/
`literature-campaign` CLI commands: **no** — they print/write JSON
directly, the same gap Phase 15/16 had, just not yet closed for these two
specific new commands (only the `campaign` command routes through the
artifact bundle). Documented here rather than glossed over.

**14. Are figures and tables reproducible?**
No new figure types were added in this phase (see final report); the
comparison-matrix table is regenerable from a list of `ComparisonRow`s,
which are themselves reproducible from a spec+seed set, same as every
other GENEVRA table.

**15. What mechanisms remain unsupported?**
- Literature `LEVEL_3_MECHANISTIC`/cross-case meta-analysis, and a
  general `observed`/`inferred`/`hypothesized` evidence-graph extension
  of `ResearchMemory` — not built (see `docs/literature_at_scale.md`).
- Parallelism beyond `worker_count=1` (`CampaignRunner`'s
  `ProcessPoolExecutor` path) exists but was not exercised in live
  validation because it requires a module-level, picklable `run_fn` — the
  CLI's `run_fn` closures are not picklable, so `genevra campaign` always
  runs sequentially. Documented as a real gap, not silently worked around.
- `boundary-search`/`literature-campaign` CLI output does not (yet) route
  through the artifact bundle (see #13).

**16. What findings remain inconclusive?**
Every live literature result in this session (CASE A at multiple periods
and seed counts) was `INCONCLUSIVE`. This is not being reported as
evidence against the underlying claim — only as "not enough signal at
this sample size," exactly the distinction Phase 11 built the label set
to preserve.

**17. Which questions are now strong enough for a final research campaign?**
None yet. The machinery (campaigns, boundary search, quality levels,
leakage-safe prediction) is validated at smoke-test scale; a genuine
answer to any of Phase 15-18's scientific questions (does ecological
pressure change evolvability? does plasticity predict future novelty?)
requires running this machinery at `STANDARD`/`RESEARCH` `CampaignMode`
sizes, which this phase built but did not itself execute.
