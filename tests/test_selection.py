import numpy as np
import pytest

from genevra.evolution.selection import (
    ElitistSelection,
    FitnessProportionalSelection,
    TournamentSelection,
)


def test_fitness_proportional_selection_is_deterministic_given_seed() -> None:
    scores = [1.0, 5.0, 2.0, 8.0]
    strategy = FitnessProportionalSelection()
    a = strategy.select(scores, num_parents=6, rng=np.random.default_rng(0))
    b = strategy.select(scores, num_parents=6, rng=np.random.default_rng(0))
    assert a == b
    assert all(0 <= i < len(scores) for i in a)


def test_fitness_proportional_selection_favors_higher_fitness() -> None:
    scores = [0.0, 0.0, 0.0, 1000.0]
    strategy = FitnessProportionalSelection()
    selected = strategy.select(scores, num_parents=200, rng=np.random.default_rng(0))
    assert selected.count(3) > selected.count(0)


def test_fitness_proportional_selection_handles_negative_scores() -> None:
    scores = [-5.0, -3.0, -1.0]
    strategy = FitnessProportionalSelection()
    selected = strategy.select(scores, num_parents=10, rng=np.random.default_rng(0))
    assert all(0 <= i < len(scores) for i in selected)


def test_tournament_selection_always_returns_valid_indices() -> None:
    scores = [1.0, 2.0, 3.0, 4.0, 5.0]
    strategy = TournamentSelection(tournament_size=3)
    selected = strategy.select(scores, num_parents=10, rng=np.random.default_rng(0))
    assert len(selected) == 10
    assert all(0 <= i < len(scores) for i in selected)


def test_tournament_selection_tends_to_pick_higher_fitness() -> None:
    scores = [0.0, 0.0, 0.0, 100.0]
    strategy = TournamentSelection(tournament_size=4)  # whole population each tournament
    selected = strategy.select(scores, num_parents=20, rng=np.random.default_rng(0))
    assert all(i == 3 for i in selected)  # index 3 always wins with tournament_size == n


def test_elitist_selection_always_includes_the_best() -> None:
    scores = [1.0, 2.0, 100.0, 3.0]
    strategy = ElitistSelection(TournamentSelection(tournament_size=2), elite_fraction=0.25)
    selected = strategy.select(scores, num_parents=5, rng=np.random.default_rng(0))
    assert 2 in selected  # the best individual's index must appear


def test_selection_raises_on_empty_scores() -> None:
    strategy = FitnessProportionalSelection()
    with pytest.raises(ValueError):
        strategy.select([], num_parents=3, rng=np.random.default_rng(0))


def test_tournament_selection_rejects_invalid_size() -> None:
    with pytest.raises(ValueError):
        TournamentSelection(tournament_size=0)


def test_elitist_selection_rejects_invalid_fraction() -> None:
    with pytest.raises(ValueError):
        ElitistSelection(TournamentSelection(), elite_fraction=1.5)
