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

## Status: CONFOUNDED (downgraded from SUPPORTED by independent audit, 2026-09-13)

## Limitations
- An infrastructure-comparable proxy metric across two different engines, not a within-one-engine controlled ecology manipulation.
- Audit correction: the isolated condition (`EvolutionEngine` + `GridWorld`, discrete non-overlapping generations, tournament selection, `channels=2`) and the shared condition (`ContinuousEvolutionEngine` + `SharedGridWorld`, overlapping generations, birth/death reproduction, `channels=3`) differ in engine architecture, selection mechanism, generation structure, and sensory input dimensionality — not only in ecological sharing. The reported permutation p=0.0005 / Cohen's d=2.77 is a real, reproducible difference between the two pipelines' output on a shared metric, but it is confounded and cannot be attributed to ecological interaction structure specifically. It does not support "ecological interaction structure affects evolutionary dynamics" as a clean single-variable finding. See `docs/final_research_status.md` for what a corrected experiment (same engine, ecology toggled via `genevra.ecology.competition` regimes) would need to look like.

## Reproduction
Experiment ID(s): exp1_isolated_vs_shared