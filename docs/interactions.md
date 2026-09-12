# Interaction Network Analysis

Module: `genevra.ecology.interactions`, `genevra.ecology.network`.

## What an interaction record is

An `EcologicalInteraction` is derived, never inferred from correlation,
from what `SharedGridWorld`/`SpatialCompetition` already does:

- `COMPETITION`: `SpatialCompetition.last_blocked_pairs` records
  `(blocked_agent_id, winner_agent_id)` for every contested-cell event
  this step. `derive_competition_interactions` turns each pair into one
  record (`actor=blocked`, `target=winner`, `outcome=LOSE`).
- `RESOURCE_ACQUISITION`: any agent whose `StepResult.reward > 0` this
  step, tagged with which resource type (`StepResult.info["resource_type"]`).

Every record carries an `EcologicalContext` (experiment id, seed, step) so
records from different runs are never silently pooled.

## Network statistics

`InteractionNetwork` (built from a list of interactions):

- `degree()`: count of agent-agent records each node participates in.
- `density()`: `edges / (n choose 2)` over distinct actor/target pairs,
  undirected. Requires >= 2 nodes.
- `interaction_type_diversity()`: Shannon entropy (natural log) over the
  `interaction_type` distribution.

`EcologicalNetworkAnalyzer.analyze()` wraps this and adds an explicit
insufficient-data path: below 6 nodes or 6 edges, `density`/`degree` are
not computed at all (`structure_analysis_available=False`,
`insufficient_data_reason` explains why) rather than returning a number
computed on a graph too small to be meaningful.

`interaction_turnover(earlier, later)`: Jaccard distance between two
non-overlapping windows' edge sets — 0.0 identical, 1.0 completely
different.

## What is not implemented, and why

- **Modularity / nestedness**: not computed. A meaningful implementation
  needs a graph library (`networkx`/`python-louvain` or similar), which
  is not an existing GENEVRA dependency, and a hand-rolled version on
  GENEVRA's typically small interaction graphs (tens of nodes) would be
  more likely to mislead than inform. Adding proper support would mean
  adding `networkx` as an optional `[viz]`-style extra and validating its
  modularity/nestedness implementations against a known reference graph
  before trusting the output.
- **Cooperation as an interaction type**: `Action` (`genevra.simulation.
  types.Action`) has no action that transfers resources or fitness to
  another agent. Every `ControllerArchitecture.output_size` is required
  to equal `len(Action)` throughout the organism/evolution stack, so
  adding a `SHARE` action would change the action space — and therefore
  the required controller output size — for every existing genome,
  architecture, and stored result. That is a backward-incompatible
  architectural change this phase does not make. Implementing it
  properly would require: a new `Action.SHARE` member; a
  `SharedGridWorld` rule for what "share with a neighbor" means (which
  neighbor, how much, at what cost to the actor); and updating every
  architecture/config that hard-codes `output_size=len(Action)`.

## Reproducibility

`genevra ecology`/`genevra interactions` drive a small `SharedGridWorld`
with a fixed seed and print/write the resulting network statistics;
re-running with the same seed and step count reproduces the same
interaction records (the environment's RNG is seeded, and actions in the
CLI demo are drawn from that same seeded RNG).
