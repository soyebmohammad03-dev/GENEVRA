# experiments/

Runnable experiment entry points. Each experiment is a small script that
loads a config from `configs/`, seeds the run via
`genevra.utils.seeding.seed_everything`, wires up simulation + evolution +
metrics components, and writes trajectories/logs under `results/<run-id>/`.

No experiments exist yet — the core simulation, evolution, and learning
modules have not been built. This directory is scaffolded now so that
experiment code has an obvious, config-driven home from day one, rather than
being bolted on later.
