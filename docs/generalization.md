# Generalization (Phase 13.5)

`genevra.mechanisms.generalization.GeneralizationAnalyzer` evaluates one
genome across four environment categories, distinguishing them
explicitly rather than reporting one "generalization score":

| Category | Construction |
|---|---|
| `train` | the exact `GridWorldConfig` and environment seed distribution the genome is meant to have evolved under |
| `recurrent` | the same `GridWorldConfig`, a new environment seed — distributionally identical, literally unseen |
| `related_unseen` | one parameter (`resource_density`/`obstacle_density`) shifted moderately (`default_related_unseen_config`) |
| `novel` | multiple parameters shifted substantially, plus a larger grid (`default_novel_config`) |

For each environment: fitness (`FitnessFunction.compute`), an
`AdaptationCurve` (`genevra.metrics.adaptation`: initial/final competence,
learning gain), and the behavioral-signature distance from the train
environment's own behavior.

`GeneralizationProfile.retention(category)` returns
`fitness_in_category / fitness_in_train` — greater than 1 means the
genome scored *higher* in that environment than in its own training one
for this one sample; it is not evidence of a general generalization
capacity, and no aggregate across categories is computed.

## What "novel" means here

GridWorld's model has a fixed small parameter set (width/height,
resource/obstacle density, max steps, `EnvironmentDynamics`). "Novel" in
this module is therefore a parameter shift *within* that model, not a
qualitatively different environment class — this is the operational,
bounded notion of novelty the Phase 13 brief explicitly permits
("adapted to what GENEVRA's `GridWorldConfig` can actually vary"), not a
claim of unbounded out-of-distribution generalization.

## Mechanism is not attributed automatically

This profile reports *where* performance held up or degraded; it does
not by itself say *why* (genetic robustness, lifetime learning, or
behavioral flexibility). Isolating the mechanism requires a separate
controlled comparison — e.g. re-running the same genome with
`NoLearning()` substituted for its actual `LearningRule` (see
`RobustnessAnalyzer.learning_amplification` in
`docs/robustness_plasticity_evolvability.md` for the pattern this
project already uses for that kind of ablation).

## Canalization proxy (Phase 13.9)

`canalization_proxy(profile)` is the variance of
`behavioral_distance_from_train` across the tested environment
categories for one fixed genotype. Low variance (behavior barely changes
across environments) is the operational proxy for canalization used
here; high variance is labeled flexible.

**This is not a developmental-biology canalization measurement.** GENEVRA
has no gene-regulatory network whose expression could be buffered against
perturbation — only a fixed feedforward controller plus lifetime Hebbian
learning. The proxy can only speak to *behavioral* stability across the
tested environments, never to developmental buffering in the sense the
canalization literature uses the term. This limitation is stated in the
function's own docstring, not only here.

## CLI

```
genevra generalization --seed 0
```

Builds a small genome from the baseline experiment's configuration and
prints train fitness plus each category's fitness/retention.
