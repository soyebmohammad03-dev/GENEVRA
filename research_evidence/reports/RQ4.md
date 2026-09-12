# RQ4: Does ecological interaction structure affect evolutionary dynamics?

## Research Question
Compares final genotypic diversity between isolated (single-organism-per-episode) and shared (multi-agent, resource-competing) conditions.

## Hypotheses
rq4_isolated_vs_shared_diversity

## Experimental Design
Conditions: isolated, shared
Required replication: 8 independent seeds

## Statistical Analysis
permutation_test + cohens_d, seed as replication unit

## Status: CONFOUNDED

## Limitations
- An infrastructure-comparable proxy metric across two different engines, not a within-one-engine controlled ecology manipulation.
- Audit correction (independent review, 2026-09-13): the isolated (EvolutionEngine+GridWorld, discrete generations, tournament selection, channels=2) and shared (ContinuousEvolutionEngine+SharedGridWorld, overlapping generations, birth/death reproduction, channels=3) conditions differ in engine architecture, selection mechanism, generation structure, and sensory input dimensionality, not just ecological sharing. The permutation p-value/Cohen's d recorded above are real and reproducible, but cannot be attributed to ecological interaction structure alone. See RQ4b for the same-engine correction.

## Reproduction
Experiment ID(s): exp1_isolated_vs_shared