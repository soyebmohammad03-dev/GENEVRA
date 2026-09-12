# Niche Dynamics

Module: `genevra.ecology.niches`, `genevra.ecology.competition`, `genevra.ecology.roles`.

## Resource niches

GENEVRA's shared environment (`SharedGridWorld`) has always had two
resource types (A: denser/lower-value, B: sparser/higher-value); Phase
15 did not add a third type, it added measurement of how agents actually
use the two that exist, via `StepResult.info["resource_type"]`.

For agent `i` with acquisition history `t_1, ..., t_n in {A, B}`:

- `preference_a = count(A) / n`
- `specialization = |preference_a - 0.5| * 2` (in `[0, 1]`; 0 = used both
  equally, 1 = single-type use)
- `breadth = H(counts) / ln(2)` where `H` is Shannon entropy over the
  type counts (in `[0, 1]`; 1 = maximal breadth for 2 types)

Population-level `niche_overlap = 1 - mean(|preference_a_i - preference_a_j|)`
over all agent pairs with acquisition data — 1.0 if every agent shares an
identical preference, 0.0 if maximally divergent (e.g. half exclusively-A,
half exclusively-B).

## Competition-structure metrics

See `docs/ecological_statistics.md` for `gini_coefficient`,
`pielou_evenness`, and `herfindahl_index`'s exact formulas —
`genevra.ecology.competition` applies them to per-founding-lineage
descendant-family size as a reproductive-success inequality/evenness/
concentration measure.

"Competition regime" (weak/strong/symmetric/asymmetric/resource-limited/
spatial) is not a new mechanism: it is which `SharedGridWorldConfig`
values (`resource_a_density`, `max_agents`, ...) or which
`genevra.ecology.spatial` regime a caller chooses. This module only
measures the outcome.

## Ecological roles

`genevra.ecology.roles.classify_roles` assigns `SPECIALIST`/`GENERALIST`
(from `NicheProfile.specialization`, thresholded against the
population's own median) and `COMPETITOR` (from competition-event count
relative to the population median) — every threshold is the population's
own median at analysis time, not a fixed absolute cutoff. `confidence` is
how far the deciding metric was from the median, normalized by the
median itself (capped at 1.0) — a relative-distinctiveness score, not a
probability.

**Not implemented**: `EXPLORER` (needs a per-agent behavioral signature
computed *during* a continuous run, tied back to agent id —
`genevra.metrics.behavior.behavioral_signature` currently only operates
on a single-lifetime observation log), `COOPERATIVE_PARTICIPANT` (no
cooperation mechanism exists, see `docs/interactions.md`),
`OPPORTUNIST`/`STABILIZER` (would need per-individual tracking of
whether resource-use or behavior changes over that individual's own
lifetime, which is not currently recorded — only per-lineage
learning-strategy-at-birth is).

## Regime transitions

`genevra.ecology.regime_transitions.detect_ecological_regime_transitions`
reuses `genevra.analysis.regime_detection.detect_change_points`
unchanged, and attaches one of a small set of candidate labels
(`diversity_collapse`, `coexistence_emergence`, `competitive_exclusion`,
`specialization_burst`, `niche_separation`, `network_restructuring`,
`recovery`) based only on whether the metric decreased or increased at
the detected change point — a fixed, documented lookup table
(`_LABEL_RULES`), not a numeric magic threshold. Every transition's
`confidence` field is literally the string `"candidate"`: this module
never asserts a transition is confirmed.
