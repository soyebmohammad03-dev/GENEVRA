"""Phase 16.6: a Learning x Ecology x Environment experiment matrix.

Deliberately built as small, explicit condition factories rather than a
generic N-dimensional grid generator — the axes and levels below are
exactly what GENEVRA's existing engine can honestly instantiate (see
each factory's docstring). "Evolvable" vs "fixed" learning is not two
different `LearningRule` classes: `NoLearning` never touches
`learning_genes` at all, `HebbianLearning` always uses whatever
`learning_genes` mutation gave it — so the axis levels here are
`NoLearning` vs `HebbianLearning`, not a fixed/evolvable distinction
GENEVRA's organism model does not actually implement as two variants of
the same rule.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from enum import StrEnum

from genevra.ecology.spatial import (
    Metapopulation,
    MigrationConfig,
    SpatialRegime,
    build_connectivity,
)
from genevra.evolution.continuous import ContinuousEvolutionConfig
from genevra.organism.genome import ControllerArchitecture
from genevra.organism.learning import HebbianLearning, LearningRule, NoLearning
from genevra.organism.organism import OrganismConfig
from genevra.simulation.dynamics import EnvironmentDynamics, EnvironmentRegime, StaticDynamics
from genevra.simulation.shared_grid_world import SharedGridWorldConfig


class LearningAxis(StrEnum):
    NO_LEARNING = "no_learning"
    HEBBIAN = "hebbian"


class EcologyAxis(StrEnum):
    ISOLATED = "isolated"
    """One patch, `max_agents` == `initial_population` (no room for
    competitive turnover beyond replacement)."""
    SHARED_COMPETITION = "shared_competition"
    """One patch, standard `SharedGridWorldConfig` resource densities."""
    SPATIAL = "spatial"
    """Two `CONNECTED`-regime patches with migration."""


class EnvironmentAxis(StrEnum):
    STATIC = "static"
    """`StaticDynamics` (constant regeneration probability)."""


class MatrixMode(StrEnum):
    PILOT = "pilot"
    STANDARD = "standard"
    RESEARCH = "research"


@dataclass(frozen=True)
class MatrixModeSizing:
    total_steps: int
    initial_population: int
    max_population: int
    n_seeds: int


_MODE_SIZING: dict[MatrixMode, MatrixModeSizing] = {
    MatrixMode.PILOT: MatrixModeSizing(
        total_steps=50, initial_population=4, max_population=8, n_seeds=2
    ),
    MatrixMode.STANDARD: MatrixModeSizing(
        total_steps=200, initial_population=8, max_population=16, n_seeds=5
    ),
    MatrixMode.RESEARCH: MatrixModeSizing(
        total_steps=1000, initial_population=16, max_population=32, n_seeds=10
    ),
}


def _learning_rule_factory(axis: LearningAxis) -> Callable[[], LearningRule]:
    return NoLearning if axis is LearningAxis.NO_LEARNING else HebbianLearning


def _dynamics(axis: EnvironmentAxis) -> EnvironmentDynamics:
    if axis is EnvironmentAxis.STATIC:
        return StaticDynamics(EnvironmentRegime(resource_regen_prob=0.02))
    raise ValueError(f"unsupported environment axis {axis!r}")


def build_strategy_ecology_matrix(
    architecture: ControllerArchitecture,
    organism_config: OrganismConfig,
    mode: MatrixMode,
    base_width: int = 8,
    base_height: int = 8,
) -> dict[str, Callable[[int], ContinuousEvolutionConfig]]:
    """Returns `{condition_id: seed -> ContinuousEvolutionConfig}` for
    every (learning, ecology, environment) combination over the
    single-patch ecology levels (`ISOLATED`, `SHARED_COMPETITION`) — 2
    learning x 2 ecology x 1 environment = 4 conditions. `EcologyAxis.
    SPATIAL` is deliberately excluded: it needs a `Metapopulation`, not a
    single `ContinuousEvolutionConfig` — use
    `build_metapopulation_condition` for that condition instead."""
    sizing = _MODE_SIZING[mode]
    conditions: dict[str, Callable[[int], ContinuousEvolutionConfig]] = {}
    single_patch_ecology = (EcologyAxis.ISOLATED, EcologyAxis.SHARED_COMPETITION)

    for learning_axis in LearningAxis:
        for ecology_axis in single_patch_ecology:
            for env_axis in EnvironmentAxis:
                condition_id = f"{learning_axis.value}__{ecology_axis.value}__{env_axis.value}"

                def factory(
                    seed: int,
                    learning_axis: LearningAxis = learning_axis,
                    ecology_axis: EcologyAxis = ecology_axis,
                    env_axis: EnvironmentAxis = env_axis,
                ) -> ContinuousEvolutionConfig:
                    # ISOLATED caps population at its starting size (replacement
                    # only, no competitive turnover beyond it); both the engine's
                    # max_population and the environment's max_agents must agree,
                    # or the environment raises once a birth exceeds its capacity.
                    max_population = (
                        sizing.initial_population
                        if ecology_axis is EcologyAxis.ISOLATED
                        else sizing.max_population
                    )
                    env_cfg = SharedGridWorldConfig(
                        width=base_width,
                        height=base_height,
                        max_agents=max_population,
                        dynamics=_dynamics(env_axis),
                    )
                    return ContinuousEvolutionConfig(
                        total_steps=sizing.total_steps,
                        initial_population=sizing.initial_population,
                        max_population=max_population,
                        environment_config=env_cfg,
                        architecture=architecture,
                        organism_config=organism_config,
                        reproduction_energy_threshold=organism_config.initial_energy * 1.5,
                        offspring_energy_cost=organism_config.initial_energy * 0.4,
                        seed=seed,
                        learning_rule_factory=_learning_rule_factory(learning_axis),
                    )

                conditions[condition_id] = factory
    return conditions


def build_metapopulation_condition(
    architecture: ControllerArchitecture,
    organism_config: OrganismConfig,
    mode: MatrixMode,
    learning_axis: LearningAxis,
    base_width: int = 8,
    base_height: int = 8,
    n_patches: int = 2,
) -> Callable[[int], Metapopulation]:
    """The `EcologyAxis.SPATIAL` condition needs a `Metapopulation`, not
    a single `ContinuousEvolutionConfig` — kept as a separate factory
    rather than forcing `build_strategy_ecology_matrix`'s return type to
    accommodate both shapes."""
    sizing = _MODE_SIZING[mode]

    def factory(seed: int) -> Metapopulation:
        env_cfg = SharedGridWorldConfig(
            width=base_width, height=base_height, max_agents=sizing.max_population
        )
        patch_configs = [
            ContinuousEvolutionConfig(
                total_steps=sizing.total_steps,
                initial_population=sizing.initial_population,
                max_population=sizing.max_population,
                environment_config=env_cfg,
                architecture=architecture,
                organism_config=organism_config,
                reproduction_energy_threshold=organism_config.initial_energy * 1.5,
                offspring_energy_cost=organism_config.initial_energy * 0.4,
                seed=seed + patch_index,
                learning_rule_factory=_learning_rule_factory(learning_axis),
            )
            for patch_index in range(n_patches)
        ]
        connectivity = build_connectivity(SpatialRegime.CONNECTED, n_patches)
        migration = MigrationConfig(
            migration_probability=0.1, migration_interval=10, connectivity=connectivity
        )
        return Metapopulation(patch_configs, migration, seed=seed)

    return factory


def seed_schedule(mode: MatrixMode, base_seed: int = 0) -> tuple[int, ...]:
    """Deterministic seed sequence for a given mode — the same base_seed
    always produces the same seeds (`genevra.utils.seeding`'s
    determinism convention, applied here as a simple offset sequence
    since these seeds only need to be distinct and reproducible, not
    drawn from a shared RNG stream)."""
    sizing = _MODE_SIZING[mode]
    return tuple(base_seed + i for i in range(sizing.n_seeds))


__all__ = [
    "LearningAxis",
    "EcologyAxis",
    "EnvironmentAxis",
    "MatrixMode",
    "MatrixModeSizing",
    "build_strategy_ecology_matrix",
    "build_metapopulation_condition",
    "seed_schedule",
]
