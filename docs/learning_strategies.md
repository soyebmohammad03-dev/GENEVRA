# Learning Strategies (Phase 9)

## What a "learning strategy" is

`genevra.organism.learning` already draws the line between three things:
inherited controller weights (group A), lifetime-only plastic state
(group B), and heritable control of *how* lifetime learning happens
(group C — `LearningParams`, from `genome.learning_genes`). A **learning
strategy** (`genevra.analysis.learning_strategy.LearningStrategy`) is
group C, exposed in a form suitable for comparison, clustering, and
population-level analysis, kept independent of both A and B.

Only the three dimensions GENEVRA actually implements behavior for are
represented: `learning_rate`, `plasticity_gate`, `decay` (see
`HebbianLearning`). No additional dimensions (exploration tendency,
adaptation threshold, learning persistence, ...) were added in Phase 9 —
every parameter in a `LearningStrategy` corresponds to real, tested
behavior in `genevra.organism.learning`, not a placeholder gene.

Two organisms can share a `LearningStrategy` while their controller
weights differ arbitrarily, and vice versa — this is by construction
(`LearningStrategy.from_genome` reads only `learning_genes`, developed
through the one genotype-to-phenotype map,
`genevra.organism.phenotype.develop`).

## Comparing strategies

`WeightedStrategyDistance` computes distance over the three interpretable
dimensions (never over raw genome vectors), with configurable per-
dimension weights. `learning_strategy_diversity` is the mean pairwise
distance across a population, reusing
`genevra.metrics.diversity.mean_pairwise_distance`.

## Population structure: clusters, not a single mean

A population mean learning rate can hide the fact that two very
different strategies coexist (e.g. "high plasticity / low exploration"
vs. "low plasticity / high exploration"). `genevra.analysis
.strategy_clustering.KMeansClusterer` partitions a population into
**strategy clusters** — a from-scratch, reproducible k-means over 3-D
strategy vectors (no scikit-learn dependency). `select_k` is a simple
elbow heuristic for choosing how many clusters to use; it is a heuristic,
not a statistical test, and its result should be treated as a starting
point for investigation.

**A "strategy cluster" is never a "species."** Cluster labels are
integers with no biological meaning.

`genevra.evolution.lineage.LineageEvent` now records each individual's
`learning_strategy` (a 3-tuple) at birth, so strategy persistence,
turnover, and lineage survival (`strategy_lineage_survival`,
`strategy_turnover` in `genevra.analysis.strategy_clustering`) can be
computed directly from existing lineage records without retaining every
historical genome.

## Counterfactual perturbation, not causal proof

`genevra.analysis.counterfactual.CounterfactualAnalyzer` answers "what
happens if I perturb this genotype's learning rate/plasticity gate/
decay by a controlled amount," as distinct from
`genevra.metrics.evolvability.EvolvabilityAnalyzer`'s "what does random
mutation produce." Every `CounterfactualResult` keeps the *mechanism*
(which gene, how much) and the *outcome* (behavioral distance, fitness
delta, novelty delta) as separate fields, and documents in its own
`limitation_note` that this is controlled-perturbation analysis on one
genotype, not proof the mechanism drives the outcome under selection.
