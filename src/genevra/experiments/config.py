from __future__ import annotations

from dataclasses import dataclass

from genevra.evolution.engine import EvolutionConfig


@dataclass(frozen=True)
class ExperimentConfig:
    """A named `EvolutionConfig`. Composition rather than duplicating
    `EvolutionConfig`'s fields, so seed/generations/etc. have exactly one
    source of truth."""

    name: str
    evolution: EvolutionConfig
