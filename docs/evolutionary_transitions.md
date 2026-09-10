# Evolutionary Regime Detection & Transitions (Phase 9)

## Change-point analysis

`genevra.analysis.regime_detection.detect_change_points` finds candidate
discontinuities in a single metric's trajectory (fitness, novelty,
diversity, evolvability, learning-strategy diversity, ...): recursive
binary segmentation using a scale-normalized (CUSUM-style) mean-shift
statistic, with significance assessed by permutation test (shuffle the
series, recompute the best split, compare to the observed statistic —
the same non-parametric approach `genevra.analysis.aggregation
.permutation_test` uses elsewhere in this codebase). Every threshold is
an explicit field on `ChangePointConfig` — `min_segment_length`,
`significance_level`, `num_permutations`, `max_change_points` — so
sensitivity analysis (rerunning with different thresholds) is just
constructing a different config.

## Candidate transitions

`detect_regime_transitions` runs change-point detection independently
per metric and wraps each significant change point in an
`EvolutionaryTransitionRecord`: experiment, seed, generation, a
heuristic `transition_type` label (e.g. `novelty_burst`,
`diversity_collapse`, `learning_strategy_turnover`, or the generic
`regime_change` fallback for unrecognized metric names), the
`ChangePoint` evidence itself, and space for `lineages`/
`strategy_clusters`/`configuration` a caller can attach.

**None of this proves a causal event.** Every `EvolutionaryTransitionRecord`
carries an explicit `note` saying so. A transition record is a candidate
for investigation — via `genevra.analysis.counterfactual`, a follow-up
experiment (`genevra.discovery.followup`), or simply closer inspection —
never a verdict that a discrete biological event occurred at that
generation.

## Relationship to Phase 10

`genevra.discovery.phenomena` and `genevra.discovery.anomaly` build on
the same statistical vocabulary (trend slopes, robust z-scores,
change-point-style detection) to scan *across* experiments for patterns
worth turning into hypotheses. Regime detection here is the single-run,
single-metric building block; Phase 10 assembles it into a
multi-experiment discovery pipeline.
