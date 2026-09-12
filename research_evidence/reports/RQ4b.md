# RQ4b: Corrected: does ecological competition intensity affect genotypic diversity within one engine?

## Research Question
Same-engine correction of RQ4. Both conditions use ContinuousEvolutionEngine + SharedGridWorld with identical architecture, organism config, mutation, reproduction thresholds, and seed sequence; only resource_a_density (competition intensity for a shared resource) differs: 0.30 (minimal_competition) vs. 0.05 (shared_competition).

## Hypotheses
rq4b_competition_intensity_diversity

## Experimental Design
Conditions: minimal_competition, shared_competition
Required replication: 20 independent seeds

## Statistical Analysis
permutation_test + cohens_d, seed as replication unit (analysis plan frozen in configurations/rq4_corrected_analysis_plan.json before execution)

## Status: NOT_SUPPORTED

## Limitations
- n=24 per condition; only one manipulated parameter (resource_a_density) and one metric (genotypic_diversity) were tested — a null here does not rule out an effect via a different ecological parameter (e.g. max_agents, spatial structure) or a different metric.
- agreement_fraction=0.5 across seeds (12 of 24 sign reversals) — see statistics/rq4_corrected.json for whether a near-zero pooled effect reflects genuine seed-to-seed disagreement.
- This experiment tests association only; no causal design (e.g. a within-run intervention) was used.

## Reproduction
Experiment ID(s): exp_ecology_corrected