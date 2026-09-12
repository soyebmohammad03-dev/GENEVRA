# Phase 15/16 Scientific Quality Gate

Answering the 14 questions the Phase 15+16 specification requires before
declaring this work complete. Honest answers, including "no" and
"partially," are the point of this document.

**1. Are interactions real mechanisms or merely labels?**
Real, but narrow. `COMPETITION` and `RESOURCE_ACQUISITION` are derived
directly from `SpatialCompetition.last_blocked_pairs` and
`StepResult.info["resource_type"]` — actual simulator state, not labels
attached after the fact. `COOPERATION` is not a label pretending to be a
mechanism — it is absent entirely, documented as absent, because
GENEVRA's `Action` space has no transfer action (see `docs/interactions.md`).

**2. Are ecological roles derived from measured behavior?**
Yes, for the three roles that exist (`SPECIALIST`/`GENERALIST`/
`COMPETITOR`): each comes from `NicheProfile.specialization` or
competition-event counts, thresholded against the population's own
median at analysis time. `EXPLORER`/`COOPERATIVE_PARTICIPANT`/
`OPPORTUNIST`/`STABILIZER` are not implemented rather than approximated
with a weaker proxy — see `docs/niche_dynamics.md` for exactly what data
each would need.

**3. Is co-evolution actually implemented?**
A real, honest version: two founding sub-populations sharing one
environment and resource pool, tracked separately via lineage ancestry,
with population size and mean learning strategy reconstructed
per-species over time. It is not two biologically distinct species and
is documented as such (`docs/co_evolution.md`). It is not N-species
co-evolution, and there is no direct inter-species interaction mechanism
beyond shared resource competition.

**4. Is spatial structure meaningful?**
Yes: `Metapopulation` runs genuinely separate `ContinuousEvolutionEngine`
patches (own grid, population, lineage), and migration actually moves
genomes between them (`ContinuousEvolutionEngine.emigrate`/
`spawn_migrant`), verified in `tests/test_ecology.py::
test_metapopulation_migration_moves_individuals` (asserts
`total_migrations > 0`) and `test_metapopulation_fragmented_never_migrates`
(asserts a `FRAGMENTED` regime produces exactly 0 migrations). The
observation boundary is untouched — no organism senses patch identity.

**5. Is migration actually changing population structure?**
Yes, empirically checked, not merely assumed: the live-validation run
(see final report) showed different final population sizes/diversity
between `FRAGMENTED` and `CONNECTED` regimes at the same seeds.

**6. Are population-level statistics using correct replication units?**
Yes, by construction: `genevra.population_analysis.aggregation` exists
specifically to reduce organism/generation values to one number per
independent seed before any permutation test, Cohen's d, or bootstrap CI
runs (`genevra.ecology.hypotheses.test_ecology_hypothesis`,
`PopulationRobustnessAnalyzer`, `test_lagged_prediction`,
`leave_one_seed_out` all take pre-aggregated per-seed values). See
`docs/ecological_statistics.md`.

**7. Are current evolvability measures predictive of future outcomes?**
Not established — only the *machinery* to test this exists
(`genevra.population_analysis.prediction`). The live-validation run
computed one real lagged correlation on real data (population size ->
mean energy at lag 1); it is a demonstration that the pipeline works
end-to-end on real numbers, not a validated predictive finding (n=1
seed, illustrative only).

**8. Are temporal validation tests genuinely held out?**
`leave_one_seed_out` is a genuine held-out test (fit on N-1 seeds' data,
check sign on the truly unseen Nth seed) when >= 3 seeds are supplied.
`within_seed_holdout` is a weaker, always-available fallback (fit on a
seed's early generations, check sign on that same seed's later
generations) — documented as weaker in `docs/evolutionary_prediction.md`
because the two segments still come from one autocorrelated trajectory,
not two independent runs.

**9. Are perturbation experiments reproducible?**
Yes: `run_perturbation_experiment` runs against a seeded
`ContinuousEvolutionEngine`, and `perturb_resources` takes an explicit
`rng`. Re-running with the same seed reproduces the same before/during/
after windows (mechanism, not yet independently re-verified at
research scale across many seeds).

**10. Are ecological conclusions distinguishable from causal claims?**
By design: `genevra.ecology.hypotheses` labels results `ASSOCIATION_FOUND`/
`NO_ASSOCIATION_FOUND`/`INSUFFICIENT_DATA`, never "confirmed" or
"caused." Regime-transition labels are always tagged `confidence=
"candidate"`. Docs throughout this phase use "associated with," never
"causes," for correlational findings.

**11. Are all figures generated from real data?**
Yes for the two new figure types added this phase
(`plot_population_size_trajectory`, `plot_replication_consistency`) —
both take already-computed series/effect values as arguments, matching
Phase 14's existing "never runs a simulation itself" figure contract.
Neither was demonstrated with fabricated data outside of test fixtures.

**12. Is every artifact traceable to experiment + seed + configuration +
code version?**
Where artifacts are generated via the existing Phase 14
`genevra.artifacts` bundle system, yes (unchanged provenance machinery).
Phase 15/16's own CLI commands (`ecology`, `coevolution`, etc.) currently
print/write raw JSON results without routing through the full
`ArtifactDirectory`/provenance writer — that integration (wiring
ecology/population-analysis results into `research_artifacts/<id>/`) is
a real gap, listed below.

**13. Are any mechanisms still unsupported?**
Yes, explicitly, and listed here rather than glossed over:

- Cooperation / costly helping (no transfer action in `Action`).
- `EXPLORER`/`OPPORTUNIST`/`STABILIZER` ecological roles.
- Graph modularity/nestedness (no graph-library dependency).
- N-species (only 2-species) co-evolution.
- A ready-made "introduce a competing population" perturbation helper
  (composable from existing pieces, but not a single function yet).
- True predator/prey dynamics (never attempted — no mechanism in the
  organism model would make this more than a relabeled competition rule).

**14. Biggest remaining scientific limitations:**

- Phase 15/16's own CLI demonstrations run at laptop-smoke-test scale
  (tens of steps, single-digit seeds) — real findings from any of these
  mechanisms require the `population_analysis.matrix` conditions run at
  `STANDARD`/`RESEARCH` size with proper multi-seed statistical treatment,
  which this phase built the machinery for but did not itself execute at
  that scale.
- Ecology/population-analysis CLI outputs are not yet routed through the
  Phase 14 artifact-provenance bundle (item 12 above) — a real
  traceability gap for anyone trying to reproduce a specific run's exact
  output later from disk alone rather than from the printed CLI values.
- `gini_coefficient`/evenness/concentration are computed on
  descendant-family size as a reproductive-success proxy, not a directly
  tracked fitness quantity — an honest but real limitation of what
  `ContinuousEvolutionEngine` currently records per individual.
