# Negative and Inconclusive Results

GENEVRA's evidence package preserves every research question's actual outcome, including negative and inconclusive ones, rather than reporting only questions that produced a clean supporting result.

## RQ1: Environmental change, plasticity, and genetic-diversity retention
Status: **INCONCLUSIVE**
How does environmental change influence plasticity, learning, and evolvability (approximated here by standing genotypic diversity)?
- GENEVRA has no gene-regulatory-network developmental model; 'evolvability' here is approximated by standing genetic diversity, not mutational robustness.
- Single environmental regime (one PeriodicDynamics configuration) tested; the source paper explores a range of environmental change rates.

## RQ3: Does current genetic diversity predict future novelty?
Status: **NOT_SUPPORTED**
Leave-one-seed-out test of whether genotypic_diversity at generation t predicts instantaneous_novelty at t+5.
- Sign-agreement across seeds, not a magnitude/R^2 predictive benchmark.
- n_seeds=8; agreement_rate is None below 3 usable seeds.

## RQ5: Do independent runs converge on similar learning strategies?
Status: **INSUFFICIENT_DATA**
Compares the spread of independent seeds' mean learning-strategy vector at generation 0 vs. the final generation.
- Descriptive only; a single spread comparison is not a hypothesis test.
- GENEVRA's mutation/selection noise is itself a 'shared environmental constraint' independent of learning — this does not distinguish convergence from that shared constraint (Phase 17.13's caveat).

## RQ6: Which literature-inspired claims are supported in GENEVRA?
Status: **INCONCLUSIVE**
Structured comparison of GENEVRA's reproduction result against the literature-inspired claim(s) it was tested against.
- Only 1 of GENEVRA's 4 literature cases (A/B/C/D) is represented in this evidence package; B/C/D remain NOT_TESTED here (machinery exists, not run at this scale this session).

## RQ8: Can the discovery engine generate testable follow-up hypotheses?
Status: **INSUFFICIENT_DATA**
Runs PhenomenonDetector across CASE A's seeds, groups recurring phenomena into hypotheses, and generates (but does not execute) a follow-up experiment proposal.
- 'NOT_TESTED' here means hypotheses were generated but the generated follow-up experiment itself was not executed — the pipeline runs end-to-end, but the loop was not closed with a real follow-up run.

## RQ2: How does robustness relate to evolvability?
Status: **INCONCLUSIVE**
Correlates genetic robustness with mutational-neighborhood evolvability across independently sampled genotypes (seed = replication unit).
- Association only; direction of causality (if any) is not established.
- This measures 'current evolvability' (mutational neighborhood), not 'future evolvability realized over generations' — a genuinely stronger claim this evidence package does not attempt.

## RQ4b: Corrected: does ecological competition intensity affect genotypic diversity within one engine?
Status: **NOT_SUPPORTED**
Same-engine correction of RQ4. Both conditions use ContinuousEvolutionEngine + SharedGridWorld with identical architecture, organism config, mutation, reproduction thresholds, and seed sequence; only resource_a_density (competition intensity for a shared resource) differs: 0.30 (minimal_competition) vs. 0.05 (shared_competition).
- n=24 per condition; only one manipulated parameter (resource_a_density) and one metric (genotypic_diversity) were tested — a null here does not rule out an effect via a different ecological parameter (e.g. max_agents, spatial structure) or a different metric.
- agreement_fraction=0.5 across seeds (12 of 24 sign reversals) — see statistics/rq4_corrected.json for whether a near-zero pooled effect reflects genuine seed-to-seed disagreement.
- This experiment tests association only; no causal design (e.g. a within-run intervention) was used.
