# The Environment / World Engine

Module: `genevra.simulation` (`types.py`, `environment.py`, `grid_world.py`).

## Lifecycle

Every environment implements the `Environment` protocol
(`simulation/environment.py`, a `typing.Protocol`, structural — an
environment does not need to inherit from it, only to match its shape):

```python
reset(seed: int | None) -> Observation
observe() -> Observation
step(action: Action) -> StepResult
snapshot() -> <opaque state>
restore(state) -> None
metadata -> EnvironmentMetadata
```

`observe()` is idempotent — it does not advance simulation time, so
callers can inspect the current observation without side effects.
`snapshot()`/`restore()` exist for checkpointing and deterministic replay;
their return type is intentionally opaque at the protocol level (each
environment defines its own state type, e.g. `GridWorldState`) because
that state is simulator-internal and never handed to an organism.

A protocol (rather than an abstract base class) was chosen so that future
environments (hazards, multiple resource types, other organisms) can be
written as plain classes and verified structurally
(`isinstance(env, Environment)` works via `@runtime_checkable`), without
forcing every environment into one class hierarchy.

## The observation boundary

This is the central scientific requirement Phase 1 exists to satisfy: an
organism must never be able to sense more than the environment's design
permits.

`Observation` (`simulation/types.py`) has exactly one field: `local_grid`,
an egocentric window of shape `(2*radius+1, 2*radius+1, 2)` — channel 0 is
obstacle/wall presence, channel 1 is normalized resource amount. It
contains no absolute position, no step count, no RNG state, and no other
organism's information. `tests/test_observation_boundary.py` checks this
structurally (the dataclass has only that one field) and behaviorally (an
open, resource-free world looks identical from any interior cell — if
absolute position leaked in, that test would fail).

Everything else the simulator knows — the full obstacle/resource grids,
the agent's absolute position, the step counter, the RNG's internal state
— lives in `GridWorldState`, reachable only via `snapshot()`/`restore()`.
`StepResult.info` carries a small amount of the same kind of
simulator-only diagnostic data (position, step count) for logging and
tests; it is passed back to the caller of `step()`, never into an
organism's controller. Nothing in `genevra.organism` reads `StepResult.info`.

`StepResult.reward` is a *world-physics* signal (the resource energy made
available this step by an `EAT` action), not an organism's fitness or
energy budget — those are metabolism concerns
(`genevra.organism.metabolism`), kept out of the environment so that
different organisms can face different costs for the same world event.

## GridWorld: design choices

- **Bounded, not toroidal.** Moving off the edge is a no-op (the agent's
  position doesn't change), not a wraparound. Out-of-bounds cells are
  reported to the observation window as obstacles, so an organism senses
  a wall the same way it senses a rock.
- **`EAT` is a distinct action from movement.** Resources are not
  auto-consumed on arrival — an organism must sense a resource cell and
  choose to eat it, at the cost of not moving that step. This is what
  keeps the environment from having one obviously-optimal static policy:
  approach vs. eat vs. keep exploring is a real trade-off, especially once
  movement has a metabolic cost.
- **Deterministic, seeded RNG.** `GridWorld` owns exactly one
  `numpy.random.Generator`, created in `reset(seed)`. Every stochastic
  element (obstacle/resource placement at reset, resource regeneration
  each step) draws from it — there is no other source of randomness in
  the class. `snapshot()` captures `rng.bit_generator.state`;
  `restore()` puts it back, so replaying from a snapshot reproduces the
  exact same future, not just the same visible state.
- **Resource regeneration is vectorized.** Each step, `_regenerate_resources`
  computes a boolean spawn mask over the whole grid with one NumPy
  comparison rather than looping per-cell in Python.
- **Config validation.** `GridWorldConfig` is a frozen dataclass with
  `__post_init__` checks (densities in `[0, 1]`, positive sizes, etc.) —
  invalid configuration fails fast at construction, not partway through a
  run.

## Extensibility

Deliberately not built yet, but the interface does not need to change to
add them:

- **Multiple resource types / hazards.** `resources` could become
  additional channels in the local grid rather than a second grid; the
  `Observation` shape would grow, but `Environment`'s method signatures
  would not.
- **Seasonal/environmental change.** A per-step or per-episode modifier to
  `resource_regen_prob`/`obstacle_density` fits inside `step()`'s existing
  body.
- **Multi-agent interaction.** `GridWorld` currently simulates one agent.
  A multi-agent variant would extend `GridWorldState` (more positions) and
  `Observation` (whether/how other agents are sensed) — a new environment
  class, still satisfying the same `Environment` protocol.
- **Batch execution.** `VectorEnvironment` (`environment.py`) wraps a list
  of `Environment` instances and steps them together. It currently loops
  per-instance rather than fusing them into shared NumPy operations across
  environments (`ponytail:` marked in code) — correct today, and the
  natural place to fuse into batched array ops later if profiling shows
  the loop is a bottleneck at larger organism counts.

## Reproducibility

`reset(seed)` fully determines everything about a run's future *given the
same sequence of actions*: obstacle/resource placement, all resource
regeneration, and (via the observation the organism reacts to) the
resulting trajectory. `tests/test_grid_world.py::test_same_seed_is_fully_deterministic`
and `test_different_seeds_can_diverge` check both directions — identical
seeds must replay identically, and different seeds must be able to
produce different trajectories (not merely "be allowed to").
