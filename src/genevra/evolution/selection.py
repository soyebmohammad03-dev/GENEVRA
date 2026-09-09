"""Selection strategies: choose parent indices from reproductive
performance (fitness scores), never touch a genome directly.

Three configurable strategies, chosen via `EvolutionConfig.selection_strategy`
rather than hardcoded, since which selection pressure a population
experiences is itself an experimental variable GENEVRA needs to be able to
compare across runs.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol

import numpy as np


class SelectionStrategy(Protocol):
    def select(
        self, fitness_scores: Sequence[float], num_parents: int, rng: np.random.Generator
    ) -> list[int]: ...


class FitnessProportionalSelection:
    """Roulette-wheel selection. Fitness values are shifted to be
    non-negative before forming a probability distribution — raw fitness
    here can be negative (e.g. an organism that starved having eaten
    nothing) — which preserves rank order while keeping probabilities
    well-defined.
    """

    def select(
        self, fitness_scores: Sequence[float], num_parents: int, rng: np.random.Generator
    ) -> list[int]:
        scores = _require_scores(fitness_scores)
        shifted = scores - scores.min() + 1e-6
        probabilities = shifted / shifted.sum()
        chosen = rng.choice(len(scores), size=num_parents, replace=True, p=probabilities)
        return [int(index) for index in chosen]


class TournamentSelection:
    def __init__(self, tournament_size: int = 3) -> None:
        if tournament_size < 1:
            raise ValueError("tournament_size must be >= 1")
        self._tournament_size = tournament_size

    def select(
        self, fitness_scores: Sequence[float], num_parents: int, rng: np.random.Generator
    ) -> list[int]:
        scores = _require_scores(fitness_scores)
        size = min(self._tournament_size, len(scores))
        winners: list[int] = []
        for _ in range(num_parents):
            contenders = rng.choice(len(scores), size=size, replace=False)
            winner = contenders[int(np.argmax(scores[contenders]))]
            winners.append(int(winner))
        return winners


class ElitistSelection:
    """Wraps another strategy: the top `elite_fraction` of individuals by
    fitness are always selected first (deterministically, no RNG
    involved), and the remaining parent slots are filled by the base
    strategy."""

    def __init__(self, base_strategy: SelectionStrategy, elite_fraction: float = 0.1) -> None:
        if not 0.0 <= elite_fraction <= 1.0:
            raise ValueError("elite_fraction must be in [0, 1]")
        self._base = base_strategy
        self._elite_fraction = elite_fraction

    def select(
        self, fitness_scores: Sequence[float], num_parents: int, rng: np.random.Generator
    ) -> list[int]:
        scores = _require_scores(fitness_scores)
        num_elite = min(num_parents, int(np.ceil(len(scores) * self._elite_fraction)))
        elite_indices = [int(i) for i in np.argsort(-scores)[:num_elite]]
        remaining = num_parents - len(elite_indices)
        if remaining <= 0:
            return elite_indices[:num_parents]
        return elite_indices + self._base.select(fitness_scores, remaining, rng)


def _require_scores(fitness_scores: Sequence[float]) -> np.ndarray:
    if len(fitness_scores) == 0:
        raise ValueError("cannot select parents from an empty fitness score list")
    return np.asarray(fitness_scores, dtype=np.float64)
