# GENEVRA Architecture

This document describes the module boundaries: which are implemented, and
which are planned separations of concerns that future phases fill in, one
validated component at a time. See also [`environment.md`](environment.md)
and [`organism.md`](organism.md) for the design rationale behind the two
implemented layers.

## Layers

- **`genevra.simulation`** — environment dynamics: state representation,
  stepping, sensor/action interfaces for organisms. No evolution or
  learning logic lives here. (Implemented: `GridWorld`, the `Environment`
  protocol, `VectorEnvironment`. See `environment.md`.)
- **`genevra.organism`** — the digital organism: genome, phenotype,
  controller, sensors, memory, within-lifetime learning, metabolism,
  mutation, and a single-organism reproduction interface. (Implemented.
  See `organism.md`.)
- **`genevra.evolution`** — population-level search: selection, who
  reproduces with whom, population size control, recombination operators,
  and operators that act on evolvability/learning-mechanism genes
  themselves. (Planned — not yet implemented. `organism.reproduction`
  stops at a single organism's ability to produce one offspring; population
  dynamics are this layer's job.)
- **`genevra.metrics`** — measurement: fitness, behavioral novelty,
  population diversity, evolvability estimators, stagnation detectors.
  Metrics are computed from simulation/evolution state, never the reverse.
  (Planned.)
- **`genevra.experiments`** — orchestration: assembles the above from a
  config, runs a seeded simulation loop, and persists trajectories/logs.
  (Planned.)
- **`genevra.analysis`** — post-hoc analysis over persisted experiment
  outputs (comparison across runs/conditions, later: automated hypothesis
  discovery). (Planned.)
- **`genevra.utils`** — cross-cutting concerns with no research content:
  reproducible seeding, logging. (Implemented.)
- **`genevra.arrays`** — shared NumPy array type aliases (`FloatArray`,
  `BoolArray`) used across `simulation` and `organism`. (Implemented.)

## Why this separation

Evolvability is a first-class research question here, not a side effect —
so `learning` (within-lifetime) and `evolution` (across-generation) must be
distinct modules with an explicit interface between them, rather than one
hardcoded update loop. `metrics` is likewise independent of `simulation`/
`evolution` so that novelty, diversity, and evolvability measures can be
swapped or compared without touching the systems they measure.

## Status

**Phase 1 + 2 complete:** the environment/world engine (`simulation`) and
the digital organism foundation (`organism`) are implemented and tested —
see `environment.md` and `organism.md`. Population-level evolution,
metrics, experiment orchestration, and analysis (`evolution`, `metrics`,
`experiments`, `analysis`) do not exist yet; see the README's Development
Status section.
