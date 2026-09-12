# Robustness, plasticity cost, and evolvability

This document gives the exact definitions behind
`genevra.mechanisms.robustness`, `genevra.mechanisms.plasticity_cost`,
and the evolvability-related fields those modules produce, and states
plainly which of the recent literature's mechanisms (Cuypers/Rutten/
Hogeweg 2017; the plasticity-cost and robustness/evolvability papers
named in the Phase 13 brief) GENEVRA's current organism model can and
cannot represent.

## Robustness

Four independent dimensions, each a *distribution* (mean, std, 10th
percentile) of a distance/delta from an unperturbed baseline over
`num_samples` controlled perturbations of one genome:

| Dimension | Perturbation | Measured quantity |
|---|---|---|
| genetic | one-step Gaussian mutation (`GaussianMutation`) | behavioral-signature distance from the unmutated baseline |
| behavioral | repeated stochastic re-evaluation (new env/organism seeds, same genome) | behavioral-signature distance from one reference evaluation |
| fitness | one-step mutation | `\|fitness(mutant) - fitness(baseline)\|` |
| environmental | a `GridWorldConfig` parameter shift | `\|fitness(genome, perturbed_env) - fitness(genome, train_env)\|` |

`learning_amplification` is `behavioral.mean` under the genome's actual
`LearningRule` minus the same measurement under `NoLearning`, holding
every seed pairwise fixed. A positive value means lifetime learning adds
behavioral variability beyond intrinsic simulation stochasticity for
*this* genotype — it is not a general claim about learning's robustness.

Robustness is reported independently of fitness: a tight distribution
(low mean/std) indicates a stable outcome under that one perturbation
kind, nothing about whether the outcome itself is good.

## Robustness-evolvability association

`robustness_evolvability_association(robustness_scores, evolvability_scores)`
computes a Pearson correlation across sampled genotypes (≥3 pairs
required, `None` if either series is constant). It reports the number and
sign only — it does not decide between the competing hypotheses the
Phase 13 brief poses (robustness increases, decreases, or has a
nonlinear relationship with evolvability); that judgment belongs to
whoever runs the analysis at a real sample size and inspects the raw
scatter (see `plot_robustness_vs_evolvability` in
`docs/figure_system.md`).

## Plasticity cost: what GENEVRA can and cannot measure

**GENEVRA's `genevra.organism.metabolism.Metabolism` attaches no energy
cost to a nonzero `plasticity_gate` or `learning_rate`.** Those genes
only affect `HebbianLearning.effective_weights`
(`genevra.organism.learning`); `Metabolism.cost_for` depends only on the
chosen `Action`. This is a genuine limitation of the current organism
model, not an oversight in this analysis: inventing a metabolic cost here
would mean adding a new mechanism to the simulator and calling it an
analysis of an existing one.

What *is* measurable, and what `genevra.mechanisms.plasticity_cost`
actually reports: Pearson correlations between an evolved population's
`plasticity_gate` and

- `initial_competence` (pre-learning baseline performance, from
  `genevra.metrics.adaptation.compute_adaptation_curve`) — a negative
  correlation is consistent with (not proof of) plasticity trading off
  against baseline competence;
- genetic robustness mean;
- evolvability `viable_fraction`/`mean_behavioral_distance`.

Each requires ≥3 non-missing paired samples, following
`genevra.analysis.tradeoff.summarize_tradeoff`'s convention; missing data
is reported as missing (`None`), never defaulted to zero.

## Evolvability: existing vs. new

`genevra.metrics.evolvability.EvolvabilityAnalyzer` (Phase 8) already
reports mutation-neighborhood viability, behavioral-distance, and
(optionally) beneficial/neutral/deleterious fitness fractions for one
genotype's one-step neighborhood. Phase 13 does not replace this — the
new `genevra.mechanisms.mutational_landscape.MutationalLandscapeAnalyzer`
exposes the *underlying per-mutant distribution* behind that summary,
plus an explicitly-labeled, small, *sampled* two-step neighborhood (never
exhaustive — see the class docstring for exact sample-size semantics).
"Evolvability" in GENEVRA remains a measurement of mutational variation
reachable in one or two mutation steps, not a claim about adaptive
success under selection; see
`genevra.metrics.evolvability`'s own module docstring for the full
caveat, which every mechanism in this document inherits.
