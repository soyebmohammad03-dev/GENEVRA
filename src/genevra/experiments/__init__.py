"""Config-driven experiment orchestration.

An `ExperimentConfig` wraps an `EvolutionConfig` (see `genevra.evolution`)
plus a name; `ExperimentRunner.run()` executes it end to end and returns a
self-contained, JSON-serializable `ExperimentResult` — same config + same
seed reproduces the same result, since every stochastic step in
`EvolutionEngine` draws from one `numpy.random.Generator` seeded from
`EvolutionConfig.seed`.

Configuration here is Python dataclasses, not a YAML/TOML file format —
see `docs/experiments.md` for why, and what a file-based config loader
would need to add.
"""
