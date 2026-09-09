# Ecological and Temporal Richness

Modules: `genevra.simulation.shared_grid_world`, `genevra.simulation.dynamics`,
`genevra.simulation.interaction`, `genevra.evolution.continuous`.

Phase 1-4 ran every organism through its own private `GridWorld` episode —
scientifically useful (it isolates genome/learning effects from ecology),
but it cannot represent resource competition, spatial collisions, or
populations with mixed ages. This phase adds a second, parallel mode
without touching the first: `GridWorld`'s one-organism-per-episode
behavior is byte-for-byte what it always was (verified by the full Phase
1-4 test suite still passing unmodified). Isolated and shared episodes
are both legitimate experimental conditions to compare — see Experiment 1
below — not one being an "upgrade" of the other.

## SharedGridWorld: multiple organisms, one world

`SharedGridWorld` (a new class, not a modification of `GridWorld`) lets
several agents coexist: `add_agent`/`remove_agent` manage who's present,
`observe(agent_id)` returns that agent's own egocentric `Observation` (now
three channels: obstacle, resource A, resource B — see below), and
`step(actions: Mapping[agent_id, Action])` advances every present agent
by one tick together. The same information boundary as `GridWorld` holds:
`Observation` still has exactly one field, and absolute positions/the full
grid/RNG state live only in `SharedGridWorldState`, reachable via
`snapshot()`/`restore()` — an agent can never see another agent's
position, energy, or identity through anything the environment returns
(`tests/test_shared_grid_world.py::test_observation_exposes_only_local_grid_not_other_agents_or_global_state`).

## Organism-organism interaction: spatial competition

`genevra.simulation.interaction.InteractionSystem` is a narrow protocol —
given every agent's current and desired positions, resolve where they
actually end up — so future mechanisms (communication, cooperation,
predation) can be added as new implementations without `SharedGridWorld`
or the evolution engines changing. The one implementation so far,
`SpatialCompetition`, is GENEVRA's first real organism-organism
interaction: agents that aren't moving keep unconditional priority over
their own cell; among agents that are moving, ties for a contested free
cell are broken by ascending agent id (a documented, reproducible rule,
not a random bonus). Resource competition is not a separate mechanic — it
emerges from this: two agents can only compete for a resource cell by
both trying to move onto it, and `SpatialCompetition` decides who arrives.
`SharedGridWorld.interaction_events` counts how often a move was blocked
by another agent specifically (not by terrain), a minimal interaction
counter surfaced in `EcologicalSnapshot`.

## Resource ecology: two resource types

`SharedGridWorld` places two independent resource types at reset —
resource A (denser, `resource_a_value`) and resource B (sparser,
`resource_b_value`, typically worth more) — never on the same cell.
`EAT` consumes whichever is present. This gives organisms a real strategic
axis (forage broadly for common low-value resources vs. seek out rare
high-value ones) that a single resource type cannot represent, and is the
basis for later niche/specialization analysis. `Observation.local_grid`
grew a channel accordingly (obstacle, resource A, resource B — shape
`(2r+1, 2r+1, 3)`); `SensorSystem`/`OrganismConfig` gained a `channels`
parameter (default `2`, so every Phase 1-4 caller is unaffected) to
consume it.

## Environmental niches

Nothing new was built specifically labeled "niche" — a niche here is an
emergent combination of existing, already-configurable primitives:
resource type ratio, regeneration rate, obstacle layout, sensor range, and
movement cost together determine which behavioral strategies perform well
in a given region or configuration. The architecture supports this (all
of those are independently configurable), but GENEVRA does not yet detect
or label niches automatically — that is an analysis question for later,
not infrastructure this phase claims to have solved.

## Temporal dynamics: `EnvironmentDynamics`

`genevra.simulation.dynamics.EnvironmentDynamics` is a protocol —
`regime_at(step, rng) -> EnvironmentRegime` — consulted once per
environment step in place of a fixed `resource_regen_prob`. Four
implementations: `StaticDynamics` (no change — the original fixed-rate
behavior), `PeriodicDynamics` (deterministic two-regime cycle),
`RegimeChangeDynamics` (one deterministic switch), and
`StochasticDynamics` (bounded random perturbation drawn from the
environment's own seeded RNG, so it stays reproducible despite being
stochastic). Both `SharedGridWorld` and — as of this phase — `GridWorld`
itself accept an optional `dynamics` field (`GridWorldConfig.dynamics:
EnvironmentDynamics | None = None`); leaving it unset preserves the
original fixed-`resource_regen_prob` behavior exactly (verified: the full
existing Phase 1-4 test suite passes unmodified with this field added).
Environmental change is therefore observable only through what an
organism can sense (resource availability changing), independent of
organism internals, fully reproducible from a seed, and — via
`GenerationSnapshot`/`ExperimentResult.environment_summary` — recorded in
experiment metadata.

## Overlapping generations: `ContinuousEvolutionEngine`

`genevra.evolution.engine.EvolutionEngine` (Phase 3) remains the
non-overlapping discrete-generation engine, unchanged.
`genevra.evolution.continuous.ContinuousEvolutionEngine` is a new,
separate engine coexisting with it: one `SharedGridWorld` runs for many
timesteps, and individuals of different ages live in it simultaneously.
Each tick: every living organism acts once, the shared environment steps
once for all of them together, organisms whose energy reaches zero are
removed (`LineageTracker.record_death`), and — if there is population
capacity below `max_population` — one eligible organism (energy ≥
`reproduction_energy_threshold`) is chosen to reproduce, its mutated
offspring joining the same running world
(`LineageTracker.record_birth`). This is a deliberately simple first
overlapping-generations model: one birth opportunity per tick when
capacity allows, not a fully asynchronous or event-driven scheduler — but
it is enough to make "organism age" (`LivingOrganism.age_at(step)`,
tracked from `birth_step`) and "a population with mixed generations" real,
queryable properties rather than concepts that only exist between
discrete generations.

## Ecological bookkeeping

`EcologicalSnapshot` — population size, mean/std age, mean energy, births/
deaths/resource-consumed/interaction-events *since the last snapshot* — is
recorded every `log_every` steps (default `10`), not every step, so
history stays bounded regardless of run length; this is the "configurable
logging frequency" requirement. It intentionally does not carry every
individual's full state each snapshot — that would defeat the point of a
compact history — only the aggregates.

## Deliberately not built in this phase

- Hazard cells / predation / communication / cooperation / territory /
  niche construction: `InteractionSystem` and `EnvironmentDynamics` are
  designed so these can be added as new implementations later, but none
  is implemented now — scope was kept to one real interaction mechanism
  (spatial/resource competition) plus the two-resource-type ecology.
- Fully asynchronous/event-driven overlapping generations: the current
  model's one-birth-per-tick-when-capacity-allows rule is simple by
  design; a richer scheduler is future work.
- Automatic niche detection/labeling: niches emerge from configuration,
  but nothing currently identifies or names them.

## The question this phase exists to make askable, not answer

"Does ecological interaction create evolutionary novelty that would not
arise in isolated populations?" is not answered by this phase — Experiment
1 (`experiments/exp1_isolated_vs_shared.py`) is an infrastructure-
validation check that the isolated and shared pipelines both run,
reproduce, and can be compared on a shared metric (final-population
genotypic diversity), at one small configuration and a handful of seeds.
That is nowhere near sufficient evidence for the underlying research
question — see `docs/research_questions.md` for what would actually count
as evidence.
