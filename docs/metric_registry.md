# Metric Registry

This is the index the code comment in `genevra.evidence.metric_registry`
points to. Every metric here is a GENEVRA-specific operational proxy,
grounded in a specific module and a specific computation — **none of
them is biological ground truth**, and none should be read as a general
claim about evolution outside GENEVRA's own simulated model. See
`docs/final_research_quality_gate.md` and each metric's own module
docstring for that distinction in more depth.

## Metrics in the runtime registry (`genevra.evidence.metric_registry.REGISTRY`)

`REGISTRY` is deliberately **not exhaustive** — it only contains metrics
actually computed somewhere in the committed `research_evidence/`
package (`research_evidence/metrics/metric_registry.json` is its
generated JSON form). Everything below is read directly from
`genevra.evidence.metric_registry.REGISTRY` and
`genevra.mechanisms.definitions`.

| metric_id | units | aggregation level | replication level | definition |
|---|---|---|---|---|
| `fitness` | fitness units (`SurvivalResourceFitness` scale) | organism -> generation mean | seed | The scalar reward `SurvivalResourceFitness` assigns to one organism's lifetime — a weighted sum of survival steps and resources collected. Not a general biological fitness measure; specific to the one fitness function used. |
| `genotypic_diversity` | mean pairwise Euclidean distance (controller-weight space) | generation (population snapshot) | seed | Mean pairwise distance between controller-weight vectors in a population (capped random sample above a size threshold, not exhaustive enumeration). Says nothing about which variation is adaptive. |
| `instantaneous_novelty` | mean k-NN behavioral-signature distance | generation (population snapshot) | seed | Mean distance from each individual's behavioral signature to its nearest neighbors in that generation plus the running novelty archive. Relative to this run's own archive/population, not an absolute cross-run scale. |
| `robustness` | behavioral-signature distance / \|fitness delta\| (dimension-dependent) | one sampled genotype -> seed-level mean | seed | Preservation of phenotype/behavior/fitness/learned-behavior under a controlled perturbation (one-step mutation, repeated stochastic re-evaluation, or an environment-parameter shift). Reports a distribution (mean/std/p10), never inverts it into one score. Sampled, not exhaustive; not the inverse of fitness. See `genevra.mechanisms.robustness`. |
| `evolvability_mean_behavioral_distance` | mean behavioral-signature distance, one-step mutational neighborhood | one sampled genotype -> seed-level value | seed | Mean behavioral change across a genotype's one-step mutational neighborhood — a *potential* measurement (`is_realized=False`), not an observed evolutionary outcome. See `genevra.metrics.evolvability` / `genevra.mechanisms.definitions.EVOLVABILITY_PROFILE_DEFINITION`. |
| `plasticity_cost_association` | Pearson r, dimensionless [-1, 1] | sampled genotypes -> single correlation | n/a (correlational, not seed-replicated) | Pearson correlation between an evolved population's `plasticity_gate` and initial competence / genetic robustness / evolvability, computed only with >= 3 paired observations. **GENEVRA's metabolism model attaches no energetic/computational cost to `plasticity_gate` or `learning_rate`** — that mechanism does not exist in the organism model (verified directly against `src/genevra/organism/metabolism.py`, which has zero references to either field), so no metabolic-cost number is fabricated; only costs measurable from existing model quantities are reported. See `genevra.mechanisms.plasticity_cost`. |
| `generalization_retention` | ratio (fitness in category / fitness in train) | one sampled genotype per environment category | seed | Fitness/adaptation-speed/behavioral-change when a genome is evaluated in environments other than the one it evolved in (train / recurrent / related-unseen / novel). "Novel" here means a parameter shift within the same `GridWorld` model, not a qualitatively new dynamic. See `genevra.mechanisms.generalization`. |

`evolvability_profile` (`genevra.mechanisms.definitions.EVOLVABILITY_PROFILE_DEFINITION`)
is defined in code as a frozen dataclass of independently-computed
fields (mutational phenotypic variance, beneficial fraction,
novel/recurrent-environment fitness, adaptation gain) with **no default
aggregate weighting** — a caller-supplied weight mapping is required to
collapse it to a scalar, and nothing in GENEVRA does this by default.

## Metrics used elsewhere in GENEVRA, not (yet) in the runtime registry

These have real, code-grounded definitions in their own documentation —
listed here for discoverability, not restated, to avoid the two copies
drifting apart:

- **Behavioral diversity, novelty-vs-fitness-vs-evolvability
  distinctions** — `docs/metrics.md` (`genevra.metrics`).
- **Innovation events, persistence, dependency graphs, potential vs.
  realized innovation** — `docs/innovation.md` (`genevra.innovation`).
  Innovation is explicitly *not* defined as "fitness increased"; a
  detected event's `fitness_effect` field is `None` in the current
  detector rather than conflated with novelty.
- **Open-endedness diagnostics** (change/novelty/complexity potential,
  evolutionary activity) — `docs/open_endedness.md`
  (`genevra.analysis.open_endedness`, `genevra.innovation`). This module
  never emits a single "OPEN_ENDED = True/False" verdict.
- **Learning-strategy diversity/distance/clustering** —
  `docs/learning_strategies.md` (`genevra.analysis.learning_strategy`).
  Only `learning_rate`, `plasticity_gate`, `decay` are represented — the
  three dimensions GENEVRA actually implements behavior for.
- **Ecological metrics** (niche overlap/specialization, Gini
  coefficient, Pielou evenness, Herfindahl concentration) —
  `docs/ecological_statistics.md` (`genevra.ecology.competition`), which
  also states this project's replication-unit rule: the independent
  seed/run, never the individual organism, is the unit of replication
  for any cross-condition statistical claim.
- **Robustness/plasticity/generalization narrative and worked
  examples** — `docs/robustness_plasticity_evolvability.md`,
  `docs/evolutionary_mechanisms.md`, `docs/generalization.md` (Phase
  13), which motivate the definitions summarized in the table above.

## Why this split exists

`REGISTRY` backs the checksummed, machine-readable
`research_evidence/metrics/metric_registry.json` — it must only contain
metrics this repository can point to an actual generated number for.
The narrative docs above cover GENEVRA's full metric surface, including
metrics exercised in unit tests and CLI demonstrations but not (yet)
part of the curated evidence package. If a metric moves from
"demonstrated" to "used in a committed research question," it belongs
in `REGISTRY` too — see `genevra/evidence/metric_registry.py`'s own
docstring for this rule.
