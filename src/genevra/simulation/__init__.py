"""Environment/world engine: simulation state, observations, and stepping.

Environments expose only what an organism could plausibly sense
(`Observation`). Anything else — the full grid, an organism's absolute
position, RNG state — is simulator-internal and reachable only through
`snapshot()`/`restore()`, which exist for replay and checkpointing, not for
organisms.
"""
