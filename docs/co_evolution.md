# Co-Evolution

Module: `genevra.ecology.coevolution`.

## What "co-evolution" means here

Two "species" are two founding sub-populations sharing one
`ContinuousEvolutionEngine` run — one `SharedGridWorld`, one resource
pool, one selection pressure. The first half of the initial population
(by agent id) is species A, the second half species B. Every subsequent
individual's species is inherited from its ultimate founder, found by
walking `LineageEvent.parent_ids` back to the root (`_founder_species` in
`genevra.ecology.coevolution`).

**This is not a claim of biological speciation.** "Species" is a label
for "founding sub-population, tracked separately" so that two lineages
under identical ecological pressure can be compared without collapsing
them into one pooled population statistic — nothing more.

## How the trajectory is built

`build_coevolution_trajectory` reconstructs per-species population size
and mean learning strategy at a list of sample steps entirely from
`LineageTracker` records (`generation`, `death_generation`,
`learning_strategy`) — no extra per-step engine hook is needed. At each
sample step, a species' population is every member born by then and not
yet dead; its mean learning strategy is the element-wise mean of
`(learning_rate, plasticity_gate, decay)` across those members.

## What `CoEvolutionAnalyzer` reports

- `final_population_a`/`final_population_b`, and whether either species
  went extinct.
- `final_strategy_divergence`: Euclidean distance between the two
  species' final mean learning-strategy vectors, `None` if either
  species is extinct at the final sample step.

These are descriptive outcomes of one run. Whether ecological pressure
*causes* strategy divergence is not something one run (or several
non-independently-seeded runs) can establish — see
`docs/ecological_statistics.md` for the seed-as-replication-unit
requirement that would apply to any such claim.

## `genevra coevolution` CLI

Runs one small co-evolution experiment and prints the comparison. Not a
research-scale run — see `genevra.population_analysis.matrix` for
building a proper multi-seed comparison across ecology/learning/
environment conditions.

## Limitations

- Only two species (a 50/50 founder split) are supported; N-species
  co-evolution would need a configurable split, not implemented.
- The species split is by initial agent id, not by any behavioral or
  genetic criterion — it is a controlled experimental partition, not an
  emergent one.
- No mechanism currently lets one species directly affect another beyond
  shared resource competition (no predation, no direct interaction type
  specific to inter-species contact) — see `docs/interactions.md` for
  what interaction types exist.
