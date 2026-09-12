# Innovation Dynamics (Phase 12.2-12.6)

## What counts as an innovation event here

**Innovation is not defined as "fitness increased."** A behavior can be
novel without raising fitness (exploring a strategy that turns out
neutral or costly); a fitness increase can happen with no behavioral
novelty at all (e.g. a population converging harder on an already-known
good strategy). `genevra.innovation.events.InnovationEvent` keeps these
concepts structurally separate: `novelty_score` and `fitness_effect` are
different fields, and `fitness_effect` is `None` in the current detector
(see "Known limitation" below) rather than silently conflated with
novelty.

### Detection method

`detect_innovation_events(lineage_events, tracker, z_threshold=2.0,
min_cohort_size=3)`:

1. Groups `LineageEvent` records (already-recorded birth events, each
   carrying a compact heritable `learning_strategy` 3-tuple — see
   `genevra.analysis.learning_strategy.LearningStrategy` — captured at
   birth) by birth generation.
2. Within any generation whose birth cohort has at least
   `min_cohort_size` individuals and non-zero strategy variance, computes
   each individual's distance from that generation's mean strategy vector,
   divided by the cohort's pooled standard deviation (a z-like score).
3. Flags individuals at or above `z_threshold` as `InnovationEvent`s.

Generations with too few births, or with zero variance (every birth
strategy identical — e.g. under `NoLearning`, where every individual
carries the same fixed default), produce no events for that generation
rather than dividing by zero.

### Known limitation

`fitness_effect` is always `None`: `LineageEvent` does not record
per-individual fitness (only birth/death/reproduction and the
learning-strategy snapshot). A future revision could populate this by
threading per-individual fitness through `LineageTracker`, but this phase
does not fabricate a number it cannot measure from existing data.
`complexity_score` and `ecological_impact` are likewise always `None` —
GENEVRA has no complexity measure over learning strategies, and no
ecological-impact metric wired to `SharedGridWorld`'s resource-competition
data yet.

## Persistence

`InnovationEvent.persistence_duration` is `death_generation -
generation`, or `None` when the individual has no recorded death (still
alive when the lineage record ends — right-censored, not "did not
persist"). `descendant_count` is the total transitive descendant count via
breadth-first traversal of `LineageTracker.children`. Together these let
a report distinguish "produced novelty that vanished immediately"
(`descendant_count=0`, short `persistence_duration`) from
"evolutionarily consequential" (many descendants, long or unbounded
persistence) — Phase 12.3's core distinction.

## Innovation dependency graph — lineage descent, not temporal correlation

`genevra.innovation.dependency_graph.build_innovation_dependency_graph`
adds an edge `A -> B` **only** when `B`'s originating individual is an
actual genealogical descendant of `A`'s originating individual
(`LineageTracker.ancestors`), and `B` occurred at a later generation. Two
innovations that merely happened one after another in unrelated lineages
produce no edge — this is the module's explicit answer to "do not infer
causal dependency merely from temporal ordering."

Every edge still carries `INFERENCE_NOTE`:

> An edge marks that the later innovation's originating individual is a
> genealogical descendant of the earlier innovation's originating
> individual. This is evidence of opportunity ..., not proof of causal
> dependency — no counterfactual test is performed here.

A genuine causal claim ("innovation A caused innovation B to become
possible") would require perturbing A's lineage counterfactually and
checking whether B still occurs — exactly the kind of test
`genevra.analysis.counterfactual.CounterfactualAnalyzer` performs at the
single-genotype level, not (yet) wired into this graph.

## Evolutionary activity

`genevra.innovation.activity.build_activity_report` is built directly on
lineage/strategy machinery GENEVRA already has
(`genevra.analysis.strategy_clustering.strategy_lineage_survival`,
`.strategy_turnover`) rather than a new persistence data model:

- **`lineage_persistence`**: fraction of distinct founding lineages (root
  ancestors, `parent_ids == ()`) with at least one living descendant
  (`death_generation is None or death_generation > final_generation`) at
  the run's final observed generation.
- **`strategy_summaries`**: per strategy-cluster `persistence` (fraction
  of members whose `reproduced` flag is set) and `generation_span`.
- **`strategy_turnover_series`**: per consecutive generation pair, `1 -`
  (share of the next generation's birth cohort still in the previous
  generation's dominant strategy cluster).
- **`diversity_growth_decay_slope`**: least-squares slope of
  `behavioral_diversity` against generation index over the whole observed
  trajectory.

Every measurement is computed over however many generations the run
actually reached — never padded or extrapolated to a nominal generation
count a run that hit extinction or a budget did not reach.

## CLI

```bash
genevra innovation results/run.json --z-threshold 2.0 --min-cohort-size 3
genevra activity results/run.json
```
