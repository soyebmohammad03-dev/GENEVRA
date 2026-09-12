# Research Questions: What GENEVRA Measures, Investigates, and Would Need as Evidence

This document exists so GENEVRA does not become a collection of
impressive-looking graphs attached to weak conclusions. It separates four
things that are easy to blur together: what the system currently
*measures*, what it is built to eventually *investigate*, what would
*count as evidence* for a claim, and what would *not be enough*.

Nothing in this document is a claim that any research question below has
been answered. As of this phase, GENEVRA has run three small
infrastructure-validation experiments (a handful of seeds each, one
configuration each) — see `docs/experiments.md`. That establishes that the
machinery works and is reproducible. It establishes nothing about the
underlying scientific questions.

## 1. Can artificial organisms evolve better ways of learning, not just better behaviors?

**What GENEVRA currently measures:** `LearningParams.learning_rate` (from
`genome.learning_genes`) is heritable and can differ between organisms and
drift under mutation, exactly like any other gene. `mean_mutation_rate`/
`mean_mutation_sigma` in `GenerationSnapshot` track whether *mutation*
strength drifts over a run (Experiment 3 shows it can). Nothing currently
tracks whether *learning rate specifically* drifts in a directional way
over generations, or whether populations with evolved learning outperform
populations with `NoLearning` under matched conditions.

**What GENEVRA is trying to investigate:** whether selection acting on
`learning_genes` produces learning strategies (not just controller
weights) that improve lifetime performance beyond what a fixed, unlearned
controller could achieve in the same environment.

**What would count as evidence:** a controlled comparison (same
environment, same selection pressure, matched seeds) between a condition
with `HebbianLearning` and heritable `learning_rate` vs. a condition with
`NoLearning`, run for enough generations and seeds to distinguish a real
fitness/behavioral difference from run-to-run noise (via
`permutation_test` or equivalent), showing the learning condition reaches
higher fitness or more behaviorally effective strategies *for reasons
attributable to learning*, not to some confound (different effective
mutation rate, different population size, etc.).

**What would not be enough:** one run showing the learning condition's
final `mean_fitness` is numerically higher. That could be seed noise,
could be driven by an unrelated confound, and says nothing about *why*
learning helped even if it reliably does.

## 2. Can evolvability itself become an evolving property?

**What GENEVRA currently measures:** `EvolvabilityAnalyzer` gives an
operational, mutation-neighborhood snapshot for one genotype at one point
in time (mean behavioral distance of viable mutants, viable fraction).
`evolvability_over_time.sample_evolvability_over_generations` can sample
this at several generations along one run, producing a trajectory of such
snapshots. `mean_mutation_rate`/`mean_mutation_sigma` show whether raw
mutation *strength* drifts, which is a component of evolvability but not
the whole of it (evolvability also depends on the genotype-to-phenotype
map and the fitness landscape's shape near a genotype, neither of which
`mean_mutation_rate` alone captures).

**What GENEVRA is trying to investigate:** whether the *tendency to
produce viable, behaviorally diverse offspring* — not just raw mutation
rate — itself increases, decreases, or stabilizes under selection over
long runs, and whether that trend is itself heritable/selectable rather
than incidental drift.

**What would count as evidence:** an `evolvability_over_time` trajectory
across many generations (not the 3-5 point samples used for
infrastructure validation so far) showing a *sustained, non-noise*
directional trend in mean behavioral distance or viable fraction,
replicated across multiple seeds, ideally compared against a
selection-disabled control (e.g. random genetic drift with no fitness
function) to rule out "evolvability changes by drift alone regardless of
selection."

**What would not be enough:** a handful of evolvability samples at 3-4
generations in one 15-generation run (which is what this phase's
infrastructure demonstrates is *possible to compute*, not what it claims
to have *found*). Distinguishing a genuine evolvability trend from sample
noise requires many more generations and seeds than have been run so far.

## 3. Under what conditions does an evolving population keep producing novelty instead of stagnating?

**What GENEVRA currently measures:** `instantaneous_novelty` and
`mean_novelty` per generation; `StagnationAnalyzer` computes trend-based
signals (declining novelty/diversity/evolvability over a trailing window)
and an explicit, non-fitness-conflated `stagnation_score`. `genevra.analysis.aggregation`
can aggregate these across seeds/conditions.

**What GENEVRA is trying to investigate:** which configurable variables
(mutation strength heritability, environmental change, ecological
interaction, population size, selection pressure) causally affect whether
novelty/diversity trends decline (stagnate) or persist over long runs.

**What would count as evidence:** systematic sweeps over one variable at
a time (holding others fixed, matched seeds via `ComparisonRunner`),
across enough generations for a `StagnationAnalyzer` trend to be
distinguishable from noise, across enough seeds to report a distribution
rather than one trajectory, showing a reproducible relationship between
the swept variable and stagnation signals.

**What would not be enough:** running `StagnationAnalyzer` once on one
15-generation baseline run and reporting whatever `stagnation_score` comes
out (this phase does exactly that as a smoke test of the analyzer itself
— see validation results in the phase report — and that is all it is).
A single stagnation score from a single short run is a demonstration that
the detector runs, not a finding about when populations stagnate.

## 4. How do mutation, learning, memory, exploration, recombination, environmental change, and ecological interaction jointly affect innovation?

**What GENEVRA currently measures:** each of these except recombination
is independently configurable and independently measurable per-run
(mutation: `mean_mutation_rate/sigma`; learning: `learning_rate`,
`LearningRule` choice; memory: `MemorySystem` size/decay; exploration:
implicit in the stochastic action-sampling policy; environmental change:
`EnvironmentDynamics`; ecological interaction: isolated vs. shared mode,
`interaction_events`). Recombination/sexual reproduction is not
implemented (see Known Limitations, `docs/architecture.md`) — GENEVRA
currently only supports asexual, single-parent reproduction.

**What GENEVRA is trying to investigate:** how these factors interact —
whether, for example, heritable mutation strength matters more or less
depending on whether the environment is static or changing, or whether
ecological competition amplifies or dampens the effect of learning.

**What would count as evidence:** multi-factor controlled comparisons
(not just the single-variable comparisons this phase's three experiments
demonstrate), with enough seeds per cell to detect interaction effects
statistically, run over enough generations for the factors' effects to
manifest and stabilize.

**What would not be enough:** running the three single-variable
experiments in this phase in isolation and informally comparing their
outputs. None of them varied more than one factor at a time, and none
used enough seeds/generations to support a multi-factor interaction
claim even in principle.

## 5. Can evolutionary stagnation or dead-ends be detected before they happen?

**What GENEVRA currently measures:** `StagnationAnalyzer` detects a
declining trend *within* a trailing window that has already been
observed — it is not, in this version, a predictive/forecasting model. It
reports "these signals are currently declining," not "these signals will
decline N generations from now."

**What GENEVRA is trying to investigate:** whether the same declining-
trend signals, measured early in a run, are predictive of eventual
stagnation later in that same run (a genuine early-warning capability),
as opposed to being contemporaneous with it or lagging it.

**What would count as evidence:** running `StagnationAnalyzer` at
multiple points along many long runs, holding out the run's later
generations, and checking whether early declining trends actually predict
later outcomes better than chance — a held-out validation GENEVRA's
current tooling does not perform.

**What would not be enough:** the fact that `StagnationAnalyzer` can be
called at any generation index. Being callable early is a necessary
precondition for early detection, not evidence that it actually detects
anything predictively.

## Summary

Every "infrastructure-validation experiment" in this codebase
(`experiments/exp1*.py`, `exp2*.py`, `exp3*.py`, and `experiments/baseline.py`)
exists to prove the *pipeline* works — configs run, seeds reproduce,
comparisons are controlled, results serialize, metrics compute correctly —
not to answer any question in this document. Treat every printed number
from those scripts as "the machinery produced a real, computed value,"
never as "this is what GENEVRA has discovered about evolution."

## Phase 11 + 12: what was added, and what remains exploratory

Phase 11 (`genevra.literature`, see `docs/research_reproduction.md` and
`docs/falsification.md`) added a framework for encoding a published
evolutionary claim as an explicit, falsifiable
`LiteratureClaim`/`LiteratureExperimentSpec`, running it under GENEVRA's
own model assumptions via `LiteratureReproductionRunner`, and reporting a
computed label (`SUPPORTED`/`PARTIALLY_SUPPORTED`/`NOT_SUPPORTED`/
`CONTRADICTED`/`INCONCLUSIVE`/`INVALID_EXPERIMENT`) — plus alternative-
explanation templates, falsification-hypothesis generation, and a
provenance registry integrated into `ResearchMemory`. Phase 12
(`genevra.innovation`, see `docs/open_endedness.md` and
`docs/innovation.md`) added lineage-based innovation-event detection,
temporal-vs-genealogical dependency inference, GENEVRA-specific
evolutionary-activity analysis, potential-vs-realized innovation, and
trajectory/phase-space diagnostics, assembled by `OpenEndednessAnalyzer`.

**What is scientifically established by these two phases:** that the
measurement and reporting *machinery* works end-to-end — a spec runs,
produces a real computed statistical label, and a lab report assembles
real (not fabricated) innovation events, activity statistics, and
trajectory classifications from an actual run. Nothing more. The four
initial literature cases (`genevra.literature.cases`) are templates that
have been run on small (population <= 16, generations <= 20) pilot
configurations during development — those pilot runs are demonstrations
that the pipeline executes and produces valid labels, not findings about
whether GENEVRA's model actually exhibits the claimed patterns at
research scale.

**What remains exploratory:**

- Every one of the four literature cases documents an approximate mapping
  from the source paper's model to GENEVRA's own (see each case's
  `known_limitations`/`approximation_notes`); none has been run at a
  scale (seeds, generations, population size) sufficient to draw a
  confirmatory conclusion.
- Innovation-event detection is scoped to heritable learning-strategy
  outliers; it does not detect a general notion of behavioral novelty
  that leaves the learning-strategy genes unchanged.
- The innovation dependency graph reports lineage descent, which is
  evidence of *opportunity*, not a validated causal-dependency test.
- No open-endedness measurement in Phase 12 has been run over a
  sufficiently long horizon, with sufficient independent seeds, to
  support a claim about GENEVRA's long-run open-ended dynamics — every
  report explicitly states this ("finite-run proxy," "no evidence of
  saturation within the tested horizon").

**Known limitations carried over from this phase's implementation:**
`InnovationEvent.fitness_effect`/`complexity_score`/`ecological_impact`
are always `None` in the current detector (see `docs/innovation.md`);
`genevra.literature.runner`'s statistical core (`classify_evidence`)
implements only a mean-difference permutation test, so Case C's
contingency claim (properly about variance across replicate histories)
is tested via a documented, weaker mean-based proxy.

## Phase 13 + 14: what was added, and what remains exploratory

Phase 13 (`genevra.mechanisms`, see `docs/evolutionary_mechanisms.md`,
`docs/robustness_plasticity_evolvability.md`, `docs/generalization.md`)
decomposed "evolvability" into independently-measured traits: genetic/
behavioral/fitness/environmental robustness distributions
(`RobustnessAnalyzer`), a robustness-evolvability association function
that takes no position on direction, plasticity-cost associations scoped
to what GENEVRA's metabolism model can actually support, a
`GeneralizationAnalyzer` distinguishing train/recurrent/related-unseen/
novel environment categories, one-step and sampled two-step mutational-
landscape characterization, deepened learning-strategy-evolution queries
(lineage inheritance, environment dependence), quantile-threshold regime
classification, and a seven-link causal-chain scaffold whose links are
each tested independently. Phase 14 (`genevra.artifacts`, see
`docs/figure_system.md` and `docs/research_artifacts.md`) added a
publication-style figure library (10 of the 20 types the spec lists, with
the rest documented as skipped and why), CSV/Markdown/LaTeX table
export, a structured `research_artifacts/<experiment_id>/` directory with
provenance linking every file to its experiment id/seeds/git commit/
metric+analysis versions, a research artifact index, and an automated
report bundle — plus `genevra robustness`/`generalization`/
`analyze-mechanisms`/`figures`/`tables`/`artifacts`/`report` CLI commands.

**What is scientifically established by these two phases:** the same
kind of claim as Phase 11/12 — that the measurement and artifact-
generation *machinery* works end-to-end on real GENEVRA data. A live
`analyze-mechanisms` run against a freshly-sampled genome produces real
robustness/generalization/mutational-landscape numbers; a live
`artifacts` run against a real stored `ExperimentResult` produces real
non-trivial figure files, tables, and a report whose provenance
cross-references the same experiment id and seed set
(`tests/test_artifacts_integration.py`). Nothing about the *content* of
those numbers — whether GENEVRA's model actually exhibits a
robustness-evolvability relationship, a plasticity cost, or meaningful
generalization — has been evaluated at research scale (many seeds, many
genotypes, many conditions); every Phase 13 analyzer has so far only been
exercised on single genomes or small pilot samples during development.

**What remains exploratory:**

- Every Phase 13 analyzer operates on one genome (or a small sampled
  set) at a time; no experiment-matrix-scale run comparing conditions on
  these mechanisms has been performed.
- The robustness-evolvability association, and every plasticity-cost
  association, is reported with no fixed sign or magnitude claim — the
  actual direction found on any given sample is not evidence of a
  general GENEVRA-wide relationship until replicated across many
  independent genotypes/seeds.
- `canalization_proxy` is a behavioral-stability-across-environments
  proxy only; GENEVRA has no gene-regulatory-network model, so it cannot
  speak to canalization in the developmental-biology sense the term
  usually carries.
- The figure/table/artifact-bundle system has been exercised on single-
  run results; multi-seed/multi-condition aggregation into these figures
  (e.g. an uncertainty band across seeds) is not yet implemented.
- Ten of the twenty figure types the Phase 14 spec lists are not yet
  implemented (see `docs/figure_system.md` for the itemized list and
  reasons) — mostly because the underlying multi-condition/multi-seed
  data they would plot does not yet exist from a default experiment run.

**Known limitations carried over from this phase's implementation:**
GENEVRA's `Metabolism` model attaches no cost to a nonzero
`plasticity_gate`/`learning_rate`, so no metabolic-cost measurement is
fabricated anywhere in `genevra.mechanisms.plasticity_cost` — only
correlational costs computable from existing quantities are reported
(see `docs/robustness_plasticity_evolvability.md`). "Novel" environments
in `GeneralizationAnalyzer` are parameter shifts within `GridWorldConfig`,
not a qualitatively different environment class.

## Phase 15 + 16: advanced ecology and population-level analysis

**What Phase 15 adds:** typed `EcologicalInteraction` records derived
from `SpatialCompetition.last_blocked_pairs` and resource-acquisition
events (`genevra.ecology.interactions`); resource-niche measurement over
the existing two resource types (`genevra.ecology.niches`);
competition-structure metrics (Gini/Pielou/Herfindahl over
descendant-family size, `genevra.ecology.competition`); real spatial
structure via multi-patch `Metapopulation` with configurable migration
(`genevra.ecology.spatial`, backed by three new `ContinuousEvolutionEngine`
public methods: `step`, `emigrate`, `spawn_migrant`); an interaction
network analyzer with an explicit insufficient-data path
(`genevra.ecology.network`); two-founding-group co-evolution
(`genevra.ecology.coevolution`); data-driven ecological roles
(`genevra.ecology.roles`); regime-transition labeling reusing the
existing change-point detector (`genevra.ecology.regime_transitions`);
and five pre-registered ecology x evolvability hypotheses
(`genevra.ecology.hypotheses`).

**What Phase 16 adds:** a seed-as-replication-unit aggregation layer
(`genevra.population_analysis.aggregation`) and population-level
robustness/evolvability analyzers built on it; lagged-prediction and
genuine train/test temporal-validation tools (`prediction.py`,
`temporal_validation.py`, including a real leave-one-seed-out holdout);
a Learning x Ecology x Environment experiment matrix with pilot/standard/
research size presets (`matrix.py`); convergent-evolution checking over
lineage ancestry (`lineage_ecology.py`); seed-level replication-consistency
reporting that surfaces sign disagreement rather than hiding it behind a
pooled p-value (`replication_consistency.py`); and controlled before/
during/after perturbation experiments with resistance and recovery
reported separately (`perturbation.py`).

**What is scientifically established:** the mechanisms themselves work —
migration genuinely moves genomes between patches and changes population
structure (live-validated: `CONNECTED` patches retained genotypic
diversity of ~6.6-9.9 after 80 steps vs. `FRAGMENTED` patches collapsing
to 0.0 at the same seeds, with 22 vs. 0 migration events), and the
niche/competition/co-evolution/perturbation pipelines produce real,
finite, reproducible numbers end-to-end (verified: reruns with the same
seed produce identical trajectories; different seeds produce genuinely
different outcomes; no NaN/Inf reached any output).

**What remains exploratory:** none of the five ecology hypotheses (H1-H5)
have been tested at a sample size (`>= 3` independent seeds per
condition, per `genevra.ecology.hypotheses`'s own minimum) sufficient to
report a real association/no-association finding — the live validation
ran small pilot-scale demonstrations of the pipeline, not a
research-grade comparison. The lagged-prediction and temporal-validation
live-validation runs used a single seed each, illustrative of the
mechanism only. See `docs/phase_15_16_quality_gate.md` for the full,
itemized honesty audit, including which mechanisms (cooperation, three
of seven listed ecological roles, graph modularity, N-species
co-evolution) are explicitly unsupported and why.
