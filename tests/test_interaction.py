import numpy as np

from genevra.simulation.interaction import SpatialCompetition
from genevra.simulation.types import Position


def test_stationary_agent_keeps_its_cell() -> None:
    system = SpatialCompetition()
    current = {0: Position(1, 1), 1: Position(2, 1)}
    desired = {0: Position(1, 1), 1: Position(1, 1)}  # agent 1 tries to move onto agent 0
    obstacles = np.zeros((5, 5), dtype=bool)
    resolved = system.resolve_movements(current, desired, obstacles, width=5, height=5)
    assert resolved[0] == Position(1, 1)
    assert resolved[1] == Position(2, 1)  # blocked, stays put


def test_lower_agent_id_wins_contested_free_cell() -> None:
    system = SpatialCompetition()
    current = {5: Position(0, 0), 2: Position(2, 0)}
    desired = {5: Position(1, 0), 2: Position(1, 0)}  # both move into (1,0)
    obstacles = np.zeros((3, 3), dtype=bool)
    resolved = system.resolve_movements(current, desired, obstacles, width=3, height=3)
    assert resolved[2] == Position(1, 0)  # lower id wins
    assert resolved[5] == Position(0, 0)  # blocked, stays put


def test_movement_blocked_by_obstacle() -> None:
    system = SpatialCompetition()
    current = {0: Position(0, 0)}
    desired = {0: Position(1, 0)}
    obstacles = np.zeros((3, 3), dtype=bool)
    obstacles[0, 1] = True
    resolved = system.resolve_movements(current, desired, obstacles, width=3, height=3)
    assert resolved[0] == Position(0, 0)


def test_movement_blocked_by_boundary() -> None:
    system = SpatialCompetition()
    current = {0: Position(0, 0)}
    desired = {0: Position(-1, 0)}
    obstacles = np.zeros((3, 3), dtype=bool)
    resolved = system.resolve_movements(current, desired, obstacles, width=3, height=3)
    assert resolved[0] == Position(0, 0)


def test_non_conflicting_moves_all_succeed() -> None:
    system = SpatialCompetition()
    current = {0: Position(0, 0), 1: Position(2, 2)}
    desired = {0: Position(1, 0), 1: Position(2, 1)}
    obstacles = np.zeros((5, 5), dtype=bool)
    resolved = system.resolve_movements(current, desired, obstacles, width=5, height=5)
    assert resolved[0] == Position(1, 0)
    assert resolved[1] == Position(2, 1)
