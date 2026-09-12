# RQ4: original (confounded) result vs. corrected same-engine experiment

Scientific history is preserved, not erased. The original result's numbers
are real and reproducible; only its interpretation as ecological evidence
is withdrawn.

| Experiment | Conditions | Engine(s) | Seeds | Primary metric | Effect (Cohen's d) | Raw p | Status | Reason |
|---|---|---|---|---|---|---|---|---|
| exp1_isolated_vs_shared (original RQ4) | isolated vs. shared | Two different engines: `EvolutionEngine`+`GridWorld` (discrete generations, tournament selection, channels=2) vs. `ContinuousEvolutionEngine`+`SharedGridWorld` (continuous generations, birth/death, channels=3) | 8 | genotypic_diversity | (see statistics/rq4_ecology.json) | (see statistics/rq4_ecology.json) | CONFOUNDED | Engine architecture, selection mechanism, generation structure, and sensory input dimensionality all differ alongside ecology; the effect cannot be attributed to ecological interaction structure alone. |
| exp_ecology_corrected (RQ4b) | minimal_competition vs. shared_competition | One engine: `ContinuousEvolutionEngine`+`SharedGridWorld` for both conditions, identical architecture/config, only `resource_a_density` varied | 24 | genotypic_diversity | -0.10 | 0.7303 | NOT_SUPPORTED | Same-engine, single-variable comparison; no detectable effect found at n=24 per condition. |

The corrected experiment does not confirm the original's large effect, nor
does it retroactively prove the original effect was "caused by the engine
difference" in a formal sense — it only shows that when the engine
difference is removed, no comparable effect on this metric appears at this
sample size. Both facts stand: the original numbers are real; they do not
support the ecological claim they were originally used for.
