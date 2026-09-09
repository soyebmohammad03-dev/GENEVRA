import numpy as np

from genevra.evolution.fitness import SurvivalResourceFitness
from genevra.evolution.lifetime import LifetimeObservations
from genevra.metrics.diversity import EuclideanDistance
from genevra.metrics.novelty import NoveltyArchive
from genevra.simulation.types import Action, Position


def test_empty_archive_scores_zero() -> None:
    archive = NoveltyArchive(max_size=10, rng=np.random.default_rng(0))
    signature = np.ones(5, dtype=np.float32)
    assert archive.score(signature, EuclideanDistance()) == 0.0


def test_novel_signature_scores_higher_than_a_duplicate() -> None:
    archive = NoveltyArchive(max_size=10, rng=np.random.default_rng(0))
    reference = np.zeros(5, dtype=np.float32)
    archive.add(reference)
    archive.add(reference)
    archive.add(reference)

    duplicate = np.zeros(5, dtype=np.float32)
    far_away = np.ones(5, dtype=np.float32) * 100.0

    assert archive.score(far_away, EuclideanDistance()) > archive.score(
        duplicate, EuclideanDistance()
    )


def test_archive_respects_max_size() -> None:
    archive = NoveltyArchive(max_size=3, rng=np.random.default_rng(0))
    for i in range(10):
        archive.add(np.full(2, float(i), dtype=np.float32))
    assert len(archive) == 3


def test_novelty_is_not_fitness_under_another_name() -> None:
    """Construct two organisms with identical fitness but different
    behavior, and show novelty (distance from an archive of "typical"
    behavior) differs even though fitness does not."""
    fitness_fn = SurvivalResourceFitness(survival_weight=1.0, resource_weight=1.0)

    typical = LifetimeObservations(
        steps_survived=10,
        total_resource_gained=5.0,
        final_energy=1.0,
        positions_visited=(Position(0, 0),) * 10,
        actions_taken=(Action.STAY,) * 10,
        survived_full_lifetime=True,
    )
    unusual = LifetimeObservations(
        steps_survived=5,
        total_resource_gained=10.0,
        final_energy=1.0,
        positions_visited=tuple(Position(i, 0) for i in range(5)),
        actions_taken=(Action.MOVE_EAST,) * 5,
        survived_full_lifetime=False,
    )

    assert fitness_fn.compute(typical) == fitness_fn.compute(
        unusual
    )  # identical fitness by construction

    from genevra.metrics.behavior import behavioral_signature

    archive = NoveltyArchive(max_size=50, rng=np.random.default_rng(0))
    for _ in range(20):
        archive.add(behavioral_signature(typical))

    typical_novelty = archive.score(behavioral_signature(typical), EuclideanDistance())
    unusual_novelty = archive.score(behavioral_signature(unusual), EuclideanDistance())

    assert unusual_novelty > typical_novelty
    assert fitness_fn.compute(typical) == fitness_fn.compute(unusual)
