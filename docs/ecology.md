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

## Phase 15/16 update: typed interactions, niches, spatial patches, co-evolution

Everything above is Phase 5/6. Phase 15 (`genevra.ecology`) and Phase 16
(`genevra.population_analysis`) build on it — extending, not rewriting,
`SharedGridWorld`/`ContinuousEvolutionEngine`/`LineageTracker`.

**Typed interaction records** (`genevra.ecology.interactions`).
`SpatialCompetition` gained a `last_blocked_pairs: list[tuple[int, int]]`
instance attribute (populated on every `resolve_movements()` call,
`InteractionSystem`'s return contract unchanged) so
`derive_competition_interactions` can turn "who got blocked by whom this
step" into an `EcologicalInteraction` record: `actor`, `target`,
`interaction_type` (`COMPETITION` or `RESOURCE_ACQUISITION`), `outcome`,
provenance (`EcologicalContext`). `SharedGridWorld._attempt_eat` now
returns which resource type was consumed, surfaced as
`StepResult.info["resource_type"]`, feeding
`derive_resource_acquisition_interactions`.
`genevra.ecology.interactions.InteractionNetwork` computes degree,
density, and interaction-type diversity (Shannon entropy) from a list of
these records; `genevra.ecology.network.EcologicalNetworkAnalyzer` adds
an explicit `INSUFFICIENT_DATA`-style result (< 6 nodes or < 6 edges)
rather than a misleading density/degree number on a tiny graph, and
`interaction_turnover` (Jaccard distance between two time windows' edge
sets). **Cooperation/costly-helping is not implemented**: `Action` has no
resource/fitness-transfer action, and every controller's output size is
pinned to `len(Action)` throughout the stack — adding one would be
backward-incompatible with every existing genome/architecture/stored
result. Implementing it would mean adding an `Action.SHARE` member, a
corresponding `SharedGridWorld` transfer rule, and re-deriving every
architecture's `output_size`.

**Niches** (`genevra.ecology.niches`). Built entirely on the two resource
types that already existed — no third type was added. `NicheProfile`
tracks, per agent, `preference_a` (fraction of acquisitions that were
type A), `specialization` = `abs(preference_a - 0.5) * 2` (0 = used both
equally, 1 = single-type use), and `breadth` = normalized Shannon entropy
over the type distribution. `PopulationNicheSummary.niche_overlap` = `1 -
mean(|pairwise preference_a difference|)` across agents with data.

**Competition metrics** (`genevra.ecology.competition`), computed from a
`ContinuousEvolutionEngine` run's `history`/`LineageTracker`: population
turnover = `(total births + total deaths) / mean population size`;
`gini_coefficient` (standard formula, `None` for < 2 values or an
all-zero sample) applied to per-founding-lineage descendant-family
size as a *reproductive-success inequality* proxy (GENEVRA does not
track a per-individual scalar fitness in a continuous run — descendant
count is the closest realized-success quantity that exists);
`pielou_evenness` (Shannon entropy / ln(number of non-zero categories))
and `herfindahl_index` (sum of squared shares) over the same family-size
distribution; `lineage_survival_fraction` = fraction of generation-0
founders with a living descendant (or themselves alive) at the end.

**Spatial structure and migration** (`genevra.ecology.spatial`). Rather
than adding disconnected patches to `SharedGridWorld` itself, a spatial
regime here is multiple independent `ContinuousEvolutionEngine` patches
(own grid, population, lineage) plus a connectivity graph
(`WELL_MIXED`/`PATCHY`/`FRAGMENTED`/`CONNECTED`) controlling which
patches a migrant can move between. `ContinuousEvolutionEngine` gained
three small public methods to support this: `step()` (advance one tick,
for orchestration code that needs to interleave patches), `emigrate
(agent_id)` (remove + return the genome), and `spawn_migrant(genome)`
(introduce a genome with no local parent, not counted as a birth). No
organism senses which patch it is in or another patch's state — the
observation boundary is untouched; `Metapopulation` is simulator-level
bookkeeping exactly like grid coordinates. `diversity_by_patch()` reports
per-patch genotypic diversity and lineage persistence.

**Co-evolution** (`genevra.ecology.coevolution`). Two "species" are two
founding sub-populations sharing one `ContinuousEvolutionEngine` run
(first half of the initial population vs. the second half); every
descendant's species is its ultimate founder's species, looked up via
`LineageEvent.parent_ids` ancestry. Per-species population size and mean
learning strategy over time are reconstructed entirely from
`LineageEvent.generation`/`death_generation` — no extra per-step engine
hook needed. "Species" here means "founding sub-population, tracked
separately," not a claim of biological speciation.

**Ecological roles** (`genevra.ecology.roles`). Three roles are
data-driven: `SPECIALIST`/`GENERALIST` from `NicheProfile.specialization`
thresholded against the population's own median; `COMPETITOR` from
competition-event count relative to the population median.
`EXPLORER`/`COOPERATIVE_PARTICIPANT`/`OPPORTUNIST`/`STABILIZER` are not
implemented — see `genevra.ecology.roles`'s module docstring for exactly
what each would need (a per-agent behavioral signature computed *during*
a continuous run, a cooperation mechanism, or per-individual lifetime
behavior-change tracking, none of which currently exist).

**Regime transitions** (`genevra.ecology.regime_transitions`) reuse
`genevra.analysis.regime_detection.detect_change_points` (the existing
permutation-tested detector) and only add a post-hoc label
(`diversity_collapse`, `coexistence_emergence`, `competitive_exclusion`,
...) for what a detected change is *consistent with* — never a causal
claim, and every transition's `confidence` field is literally the string
`"candidate"`.

**Ecology x evolvability hypotheses** (`genevra.ecology.hypotheses`): five
pre-registered `EcologyHypothesis` records (H1-H5) with explicit
null/alternative/IV/DV/control/test fields, mirroring
`genevra.literature.claims.LiteratureClaim`'s convention.
`test_ecology_hypothesis` runs a permutation test + Cohen's d + bootstrap
CI on seed-level samples, returning `INSUFFICIENT_DATA` (not a fabricated
p-value) below `min_seeds` (default 3) per side.

**Population-level scaling** (`genevra.population_analysis`) — see
`docs/population_analysis.md`, `docs/evolutionary_prediction.md`,
`docs/perturbation_experiments.md`, and `docs/ecological_statistics.md`
for the rest of Phase 16.

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
