import numpy as np
import pytest

from genevra.discovery.replication import EvidenceSet, ReplicationRunner, SeedSplit, split_seeds


def test_split_seeds_produces_non_overlapping_halves() -> None:
    split = split_seeds(list(range(10)), discovery_fraction=0.5)
    assert set(split.discovery_seeds) & set(split.validation_seeds) == set()
    assert set(split.discovery_seeds) | set(split.validation_seeds) == set(range(10))


def test_seed_split_rejects_overlap() -> None:
    with pytest.raises(ValueError):
        SeedSplit(discovery_seeds=(0, 1), validation_seeds=(1, 2))


def test_replication_runner_rejects_overlapping_seeds() -> None:
    original = EvidenceSet(seeds=(0, 1, 2), values=(1.0, 1.1, 0.9), source="original")
    replication = EvidenceSet(seeds=(2, 3, 4), values=(1.0, 1.2, 0.8), source="replication")
    with pytest.raises(ValueError):
        ReplicationRunner().evaluate("h1", original, replication, np.random.default_rng(0))


def test_replication_confirms_a_consistent_positive_effect() -> None:
    original = EvidenceSet(seeds=(0, 1, 2), values=(1.0, 1.2, 0.9), source="original")
    replication = EvidenceSet(
        seeds=(100, 101, 102, 103, 104), values=(1.0, 1.1, 0.95, 1.05, 1.0), source="replication"
    )
    result = ReplicationRunner().evaluate("h1", original, replication, np.random.default_rng(0))
    assert result.replicated is True
    assert result.replication_ci.low > 0.0


def test_replication_fails_when_effect_vanishes() -> None:
    original = EvidenceSet(seeds=(0, 1, 2), values=(1.0, 1.2, 0.9), source="original")
    replication = EvidenceSet(
        seeds=(100, 101, 102, 103, 104),
        values=(0.01, -0.02, 0.03, -0.01, 0.0),
        source="replication",
    )
    result = ReplicationRunner().evaluate("h1", original, replication, np.random.default_rng(0))
    assert result.replicated is False


def test_replication_requires_at_least_two_replication_values() -> None:
    original = EvidenceSet(seeds=(0,), values=(1.0,), source="original")
    replication = EvidenceSet(seeds=(1,), values=(1.0,), source="replication")
    with pytest.raises(ValueError):
        ReplicationRunner().evaluate("h1", original, replication, np.random.default_rng(0))
