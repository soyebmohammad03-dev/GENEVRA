# Evolutionary mechanisms (Phase 13)

`genevra.mechanisms` decomposes "evolutionary potential" into
independently-measured traits — robustness, plasticity cost,
generalization, evolvability, mutational landscape, learning-strategy
evolution, regime classification, and a causal-chain scaffold — rather
than one "adaptability score." See `genevra.mechanisms.definitions` for
every trait's formal `MetricDefinition` (definition, input data, math
definition, interpretation, limitations, realized-vs-potential flag).

## Why not one score

Robustness, plasticity, evolvability, generalization, novelty, and
innovation are related but not interchangeable (Phase 13's explicit
requirement). A genotype can be robust and unfit, evolvable and fragile,
or generalize well in one environment category and poorly in another.
Every analyzer in this package returns a multidimensional profile; no
function silently averages these into a single number.

## Modules

- `genevra.mechanisms.robustness` — `RobustnessAnalyzer` measures
  genetic (behavioral distance under one-step mutation), behavioral
  (distance across repeated stochastic re-evaluations of the unmutated
  genome), fitness (`|fitness delta|` under mutation), and environmental
  (`|fitness delta|` under a `GridWorldConfig` perturbation) robustness,
  each reported as a distribution (mean/std/10th percentile), never only
  a mean. `learning_amplification` compares behavioral variance with the
  organism's actual `LearningRule` against `NoLearning`, holding seeds
  fixed — the only "learning robustness" measurement GENEVRA's current
  model supports.
- `genevra.mechanisms.robustness.robustness_evolvability_association` —
  Pearson correlation between a robustness measurement and an
  evolvability measurement across sampled genotypes. Association only;
  it takes no position on which of H1 (robustness increases
  evolvability), H2 (the opposite), or H3 (nonlinear) holds.
- `genevra.mechanisms.plasticity_cost` — correlations between an evolved
  population's `plasticity_gate` and other measured traits (initial
  competence, genetic robustness, evolvability), following
  `genevra.analysis.tradeoff`'s ≥3-paired-observations convention. See
  `docs/robustness_plasticity_evolvability.md` for why no metabolic cost
  is measured.
- `genevra.mechanisms.generalization` — `GeneralizationAnalyzer` and
  `canalization_proxy`; see `docs/generalization.md`.
- `genevra.mechanisms.mutational_landscape` — one-step (full sample) and
  optional two-step (small, explicitly-labeled *sampled*, never
  exhaustive) mutational-neighborhood characterization: neutral/
  deleterious/beneficial fractions, behavioral-distance distribution,
  viable fraction.
- `genevra.mechanisms.learning_strategy_evolution` —
  `lineage_strategy_inheritance` (parent-to-child `LearningStrategy`
  distance, built directly on `LineageTracker` records) and
  `strategy_environment_dependence` (per-condition mean evolved
  strategy, descriptive only — no significance test).
- `genevra.mechanisms.regime` — `classify_regimes` extends
  `genevra.analysis.regime_detection`/`genevra.analysis.stagnation` with
  quantile-based (not hand-picked constant) thresholds for exploration/
  exploitation/innovation_burst/adaptation/stabilization/stagnation/
  recovery/strategy_transition/environmental_response labels. A
  generation may carry multiple labels or none.
- `genevra.mechanisms.causal_chain` — `CAUSAL_CHAIN`, the seven-link
  scaffold (environmental volatility → learning strategy → lifetime
  adaptation → selection → genetic composition → mutational landscape →
  future evolvability → innovation) from the Phase 13 spec, each link
  naming the existing/new analysis that can test *that one arrow*.
  Nothing in GENEVRA tests the whole chain at once, and no code infers a
  causal chain from correlated endpoints.
- `genevra.mechanisms.report.MechanismsReport` — a `to_dict()`/`to_text()`
  bundle of whichever sections were actually computed, following the
  same convention as `genevra.discovery.report`/`genevra.literature.report`/
  `genevra.innovation.report`.

## CLI

```
genevra robustness --seed 0 --num-samples 8
genevra generalization --seed 0
genevra analyze-mechanisms --seed 0 --num-samples 8
```

Each builds a small genome from the baseline experiment's
organism/environment configuration (see `_mechanisms_setup` in
`genevra.cli`) — these commands demonstrate the analyzers on one
freshly-sampled genome, not a stored population; they are not a
replacement for a full experiment/comparison run.

## What this phase does not claim

No function in `genevra.mechanisms` establishes causation from an
association, and no analyzer here has been run at research scale (many
seeds, many genotypes) to support a scientific conclusion — see
`docs/research_questions.md`'s Phase 13/14 section for what remains
exploratory.
