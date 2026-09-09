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
