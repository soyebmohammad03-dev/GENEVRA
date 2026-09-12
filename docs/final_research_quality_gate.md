# Final Research Quality Gate (Phase 19)

Honest answers to the spec's 22 required questions, following the same
convention as `docs/phase_15_16_quality_gate.md` and
`docs/phase_17_18_quality_gate.md`. Every number cited here is from the
real `research_evidence/` package produced by
`python -m genevra.cli reproduce-evidence --mode full` on this commit.

**1. What questions can GENEVRA actually investigate?**
The eight research questions in `research_evidence/tables/research_question_matrix.md`:
environmental change vs. plasticity/diversity (RQ1), robustness vs.
evolvability (RQ2), current diversity predicting future novelty (RQ3),
isolated vs. shared ecology (RQ4), cross-seed strategy convergence
(RQ5), literature-claim support (RQ6), boundary conditions of one
literature case (RQ7), and discovery-engine hypothesis generation
(RQ8). All eight ran end-to-end on real GENEVRA simulations this
session.

**2. Which questions have enough evidence?**
Only RQ4 (ecology): 8 independent seeds, permutation p=0.0005, Cohen's
d=2.77 — `SUPPORTED`. Every other RQ ran with 3-10 seeds/genomes, which
this project's own statistical conventions (Phase 16-18) treat as
laptop-smoke-test-adjacent, not research-scale. None of RQ1/2/3/5/6/7/8
should be read as "enough evidence" for a strong claim yet.

**3. Which findings replicate across independent seeds?**
RQ4's effect direction was checked across all 8 seeds implicitly via
the permutation test's use of the full sample (not seed-by-seed sign
consistency, which was not separately computed for RQ4 this session —
a gap, not a claim of replication beyond what the permutation test
itself establishes). RQ3's leave-one-seed-out result is a genuine
per-seed replication check (agreement_rate reported directly in
`research_evidence/statistics/rq3_lagged_prediction.json`) and it did
NOT show consistent replication (status `NOT_SUPPORTED`).

**4. Which findings fail replication?**
RQ3 (diversity(t) predicting novelty(t+k)): the held-out-seed sign
agreement was low enough to classify `NOT_SUPPORTED`, not merely
inconclusive — this is a genuine negative finding for this specific
lag/metric pairing, not evidence the underlying idea is false in
general.

**5. Which findings remain inconclusive?**
RQ1 (CASE A's own reproduction), RQ2 (robustness-evolvability
correlation, r≈0.095, essentially no linear association at n=10), RQ6
(the literature comparison matrix, which is just RQ1's result
re-tabulated), and RQ7's INCONCLUSIVE points within the boundary sweep.

**6. Which metrics are predictive?**
None demonstrated predictive power this session. RQ3 is the only
executed predictive test and it did not support the tested predictor.
The machinery (`genevra.population_analysis.temporal_validation`,
`genevra.population_analysis.prediction`) exists for further predictive
benchmarking; none of it has yet produced a positive predictive result
against a held-out seed.

**7. Which relationships are only associative?**
RQ2 (robustness/evolvability) is explicitly correlational — reported as
a Pearson r, never as a causal claim, and the module docstrings
(`genevra.mechanisms.robustness`) say so directly.

**8. Which mechanisms have direct experimental support?**
Isolated-vs-shared ecology producing a genotypic-diversity difference
(RQ4) is the one result with a real, significant, large effect this
session. It is a proxy-metric comparison across two different
simulation engines (documented in `experiments/exp1_isolated_vs_shared.py`'s
own docstring), not a within-one-engine manipulation of a single
ecological parameter — a real limitation on how mechanistically it can
be interpreted.

**9. Which mechanisms remain unsupported?**
Everything already listed as unsupported in
`docs/phase_15_16_quality_gate.md` and `docs/phase_17_18_quality_gate.md`
(cooperation/costly-helping, most ecological roles, network
modularity/nestedness, N-species co-evolution, LEVEL_3 mechanistic
literature reproduction, cross-case literature meta-analysis) remains
unsupported after this phase — Phase 19 built an evidence package on
top of existing machinery, it did not add new mechanisms.

**10. Which literature patterns are reproduced?**
None, at the `SUPPORTED`/`PARTIALLY_SUPPORTED` level, this session.
CASE A's own reproduction (RQ1/RQ6) is `INCONCLUSIVE`, and the boundary
sweep (RQ7) found real transitions between labels across the tested
periods but none of the tested periods reached `SUPPORTED` either —
see `research_evidence/statistics/rq7_boundary_sweep.json` for the
literal per-value labels.

**11. Which literature patterns are not reproduced?**
None are positively `NOT_SUPPORTED`/`CONTRADICTED` either — the honest
answer for CASE A this session is "no distinguishable effect at this
sample size," which is what `INCONCLUSIVE` means, not "shown false."
CASE B/C/D were not run at evidence-package scale this session
(documented as a scope reduction).

**12. What boundary conditions were discovered?**
Real transitions were found across CASE A's environmental-change-period
sweep (periods 10/20/40, 4 seeds each) — the exact transition points
are in `research_evidence/statistics/rq7_boundary_sweep.json`. This is
a coarse, 3-point sweep with 4 seeds per point; treat any specific
transition value as illustrative, not a precisely located boundary.

**13. Which findings are sensitive to parameters?**
Not formally classified via `genevra.evidence.robustness_classifier`
against multiple independent parameter variants this session (only RQ2
got a `classify_robustness` pass, over per-genome robustness values
rather than across genuinely different parameter settings — see
`research_evidence/statistics/rq2_sensitivity.json`). The boundary
sweep (RQ7) is the closest thing to a real sensitivity check performed,
and it did find label changes across the swept parameter.

**14. Which findings survive held-out validation?**
Only RQ3 used a genuine held-out-seed test (`leave_one_seed_out`), and
it did not survive (`NOT_SUPPORTED`). No other RQ in this package used
temporal or seed holdout this session — a real gap against the spec's
ambition, disclosed rather than glossed over.

**15. Are any conclusions dependent on a particular random seed?**
RQ4's effect was computed across 8 independent seeds with a permutation
test, so it is not a single-seed artifact. RQ2's per-genome correlation
used 10 independently-seeded genomes. RQ5's convergence measurement
found `initial_mean_pairwise_strategy_distance == 0.0` — a genuinely
seed-independent artifact of GENEVRA's deterministic gene
initialization before mutation acts, not a finding about convergence
at all (see the `note` field in
`research_evidence/statistics/rq5_strategy_convergence.json`).

**16. Are any results affected by model approximations?**
Yes, throughout: CASE A's `genotypic_diversity` is an explicit proxy for
the source paper's mutational-robustness evolvability metric (no
gene-regulatory-network model exists in GENEVRA); RQ4's isolated/shared
comparison spans two different simulation engines rather than one
controlled ecological manipulation. Both are stated in the relevant
`LiteratureClaim`/experiment docstrings and repeated in the RQ reports.

**17. Are ecological effects genuinely population-level?**
RQ4's statistic (permutation test + Cohen's d over 8 seeds) is
genuinely seed-level, not organism-level — no pseudoreplication. It
does not, however, isolate which specific ecological mechanism
(resource competition, spatial interaction, or simply "more organisms
alive at once") drives the diversity difference; that decomposition
was not attempted this session.

**18. Are innovation measurements supported by actual data?**
RQ8's phenomenon-detection step ran on real trajectories and found one
real recorded phenomenon (`repeated_regime_oscillation`, seed 5) but it
did not recur across enough independent seeds to produce a hypothesis
(`n_recurring_hypotheses=0`) — see
`research_evidence/statistics/rq8_discovery.json`. No dedicated
innovation-event campaign was re-run for this evidence package; Phase
12's innovation-detection machinery was exercised in Phase 12's own
validation, not re-demonstrated here.

**19. Are open-endedness conclusions appropriately limited?**
This evidence package makes no open-endedness claim at all — none of
RQ1-RQ8 measures open-endedness metrics directly. That is a real
absence from this package, not a claim resolved elsewhere in it.

**20. What would need to be done before making biological/general claims?**
At minimum: re-run RQ1-RQ8 at `CampaignMode.RESEARCH` scale (20+ seeds
per condition, per Phase 17's own campaign modes) rather than the 3-10
used here; add a genuine pre-registered development/validation split
where the analysis plan is frozen using only development seeds before
any validation-seed data is examined (this package's seed split is a
real non-overlapping partition, but the analysis choices — lag k,
status thresholds — were fixed in code before the split existed, not
literally re-derived from a development subset); and reproduce CASE
B/C/D at the same scale as CASE A.

**21. What experiments should be repeated at larger scale?**
RQ4 (ecology) first, since it is the one result with a real effect
worth confirming holds at more seeds and a wider range of population
sizes; then RQ3 (diversity → novelty prediction) with more seeds, since
`leave_one_seed_out` needs a larger N to give a stable agreement rate.

**22. What are the strongest possible research questions for the eventual paper?**
RQ4 (does ecological interaction structure change genetic diversity
outcomes?) is currently GENEVRA's strongest real result and the most
promising basis for a focused, well-powered follow-up study — a
within-one-engine ecological manipulation (e.g. using
`genevra.ecology.competition`'s regimes on `SharedGridWorld` alone,
rather than comparing across two different engines) at
`CampaignMode.STANDARD`/`RESEARCH` scale.
