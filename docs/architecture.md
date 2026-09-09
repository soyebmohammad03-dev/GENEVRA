# GENEVRA Architecture (foundation stage)

This document describes the intended module boundaries. As of this
commit, only `genevra.utils` (seeding, logging) exists — everything else
below is the planned separation of concerns that future work will fill in,
one validated component at a time.

## Layers

- **`genevra.simulation`** — environment dynamics: state representation,
  stepping, sensor/action interfaces for organisms. No evolution or
  learning logic lives here.
- **`genevra.organism`** — the digital organism: genome representation,
  a small neural network (policy/controller), memory, and the mapping from
  genome to phenotype (development).
- **`genevra.learning`** — within-lifetime learning mechanisms (e.g.
  Hebbian updates, plastic weights, meta-learned learning rules) applied to
  an organism's network during its lifetime, separate from evolutionary
  (across-generation) search.
- **`genevra.evolution`** — population-level search: selection,
  reproduction, mutation, recombination operators, and operators that act
  on evolvability/learning-mechanism genes themselves.
- **`genevra.metrics`** — measurement: fitness, behavioral novelty,
  population diversity, evolvability estimators, stagnation detectors.
  Metrics are computed from simulation/evolution state, never the reverse.
- **`genevra.experiments`** — orchestration: assembles the above from a
  config, runs a seeded simulation loop, and persists trajectories/logs.
- **`genevra.analysis`** — post-hoc analysis over persisted experiment
  outputs (comparison across runs/conditions, later: automated hypothesis
  discovery).
- **`genevra.utils`** — cross-cutting concerns with no research content:
  reproducible seeding, logging. (Implemented.)

## Why this separation

Evolvability is a first-class research question here, not a side effect —
so `learning` (within-lifetime) and `evolution` (across-generation) must be
distinct modules with an explicit interface between them, rather than one
hardcoded update loop. `metrics` is likewise independent of `simulation`/
`evolution` so that novelty, diversity, and evolvability measures can be
swapped or compared without touching the systems they measure.

## Status

Foundation stage: project scaffolding, tooling, and reproducibility
utilities only. No simulation, organism, learning, evolution, or metrics
code exists yet — see the README's Development Status section.
