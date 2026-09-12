# RQ4b: Corrected same-engine ecological competition comparison

## Research Question
Does ecological competition intensity affect final genotypic diversity, holding the simulation engine, architecture, and every other configuration parameter fixed?

This is a same-engine correction of RQ4, which the independent audit found CONFOUNDED (it compared `EvolutionEngine`+`GridWorld` against `ContinuousEvolutionEngine`+`SharedGridWorld` — two different engines). See `research_evidence/research_questions/RQ4.json` for the original result, preserved and relabeled, not deleted.

## Pre-registered analysis plan
Frozen to `research_evidence/configurations/rq4_corrected_analysis_plan.json` *before* the experiment was executed:
- Primary outcome: `genotypic_diversity`
- Secondary outcomes: `final_population_size`, `mean_energy`
- Expected direction: undirected
- Replication unit: seed
- Minimum sample size: 20
- Statistical test: permutation_test + cohens_d

This result is labeled CONFIRMATORY.

## Experimental Design
Both conditions use `ContinuousEvolutionEngine` + `SharedGridWorld`, identical `ControllerArchitecture`, identical `OrganismConfig` (`channels=3`), identical mutation/reproduction/population settings, and the same seed sequence (0-23). The only varied parameter is `resource_a_density`:
- `minimal_competition`: resource_a_density = 0.30 (abundant resource A)
- `shared_competition`: resource_a_density = 0.05 (scarce resource A)

Seeds: 24 independent seeds per condition (0-23) — exceeds the pre-registered minimum of 20.

## Statistical Analysis
- Permutation test (shared - minimal, 5000 permutations): observed_difference = -0.2208, p = 0.7313
- Cohen's d = -0.1008 (negligible)
- Bootstrap 95% CI of the mean, shared_competition: [6.714, 8.521]
- Bootstrap 95% CI of the mean, minimal_competition: [7.043, 8.665]
- Replication consistency: agreement_fraction = 0.5, sign_reversals = 12 of 24 (seeds are genuinely split on direction, not a real effect masked by noise)
- FDR: raw p = 0.7313, BH-adjusted p = 0.8171 (family: `research_evidence/statistics/rq_family_fdr.json`, 2 confirmatory tests)

## Status: NOT_SUPPORTED

No detectable effect of this resource-scarcity manipulation on final genotypic diversity was found at n=24 per condition. The confidence intervals overlap substantially, the effect size is negligible, and seeds are split roughly 50/50 on direction.

## Limitations
- Only one ecological parameter (resource_a_density) and one metric (genotypic_diversity) were tested. A null here does not rule out an effect via a different parameter (e.g. `max_agents`, spatial structure) or a different outcome metric.
- Association only; no causal/interventional design.
- This does NOT retroactively validate or invalidate the original RQ4 comparison's numbers — those remain a separate, confounded, historical result (see the diagnostic table `research_evidence/tables/rq4_historical_vs_corrected.md`).

## Reproduction
Experiment ID: exp_ecology_corrected (`experiments/exp_ecology_corrected.py --seeds 0 1 2 ... 23`)
