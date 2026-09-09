import numpy as np

from genevra.organism.memory import MemorySystem


def test_memory_starts_at_zero() -> None:
    memory = MemorySystem(size=4)
    assert np.array_equal(memory.state, np.zeros(4, dtype=np.float32))


def test_update_changes_state_deterministically() -> None:
    memory_a = MemorySystem(size=4, decay=0.5)
    memory_b = MemorySystem(size=4, decay=0.5)
    input_vector = np.array([1.0, -1.0, 0.5, 0.5, 0.2], dtype=np.float32)
    memory_a.update(input_vector)
    memory_b.update(input_vector)
    assert np.array_equal(memory_a.state, memory_b.state)
    assert not np.array_equal(memory_a.state, np.zeros(4, dtype=np.float32))


def test_reset_returns_to_zero() -> None:
    memory = MemorySystem(size=3)
    memory.update(np.array([1.0, 2.0, 3.0], dtype=np.float32))
    memory.reset()
    assert np.array_equal(memory.state, np.zeros(3, dtype=np.float32))


def test_memory_is_not_the_genome() -> None:
    """Memory is lifetime state: two organisms with identical genomes but
    different sensory histories must diverge in memory."""
    memory_a = MemorySystem(size=4, decay=0.5)
    memory_b = MemorySystem(size=4, decay=0.5)
    memory_a.update(np.array([1.0, 1.0, 1.0], dtype=np.float32))
    memory_b.update(np.array([-1.0, -1.0, -1.0], dtype=np.float32))
    assert not np.array_equal(memory_a.state, memory_b.state)
