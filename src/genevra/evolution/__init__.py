"""Population-level evolution: many organisms, discrete generations,
selection, reproduction, mutation, and ancestry tracking.

This is where GENEVRA becomes an evolving population rather than a
collection of independent organisms (see `genevra.organism`). Population
logic is deliberately not coupled to a specific environment: `lifetime.py`
runs one organism in one environment instance and returns a plain
`LifetimeObservations` record; everything above that (fitness, selection,
reproduction, lineage) operates on those records and on `Genome` objects,
never on environment internals directly.

The first implementation uses non-overlapping discrete generations: each
generation's individuals live out one lifetime, then are entirely replaced
by their selected offspring. Overlapping generations, continuous-time
evolution, sexual reproduction/recombination, ecological interaction
between organisms sharing one environment, speciation, and migration
between environments are not implemented — see docs/architecture.md for
where each would plug in without redesigning this package.
"""
