# configs/

Versioned, declarative configuration for experiments (environment
parameters, population size, mutation rates, learning rule choice, random
seed, etc.). Experiments must be reproducible from a config file plus a
seed — no experiment-defining parameters should be hardcoded in scripts.

No configs exist yet; the config schema will be defined alongside the first
real experiment, once the simulation and evolution modules it configures
exist. A schema written before that would be a guess.
