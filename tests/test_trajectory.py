from genevra.metrics.fitness_metrics import FitnessSummary
from genevra.metrics.trajectory import GenerationSnapshot, Trajectory


def make_snapshot(generation: int) -> GenerationSnapshot:
    return GenerationSnapshot(
        generation=generation,
        fitness_summary=FitnessSummary(n=5, mean=1.0, median=1.0, max=2.0, min=0.0, std=0.5),
        genotypic_diversity=0.3,
        behavioral_diversity=0.4,
        mean_novelty=0.1,
        instantaneous_novelty=0.05,
        survival_rate=0.8,
        reproductive_success_rate=0.5,
        mean_mutation_rate=0.1,
        mean_mutation_sigma=0.2,
        genome_centroid_shift=None,
        behavior_centroid_shift=None,
        extinction=False,
    )


def test_trajectory_preserves_append_order() -> None:
    trajectory = Trajectory()
    trajectory.append(make_snapshot(0))
    trajectory.append(make_snapshot(1))
    assert len(trajectory) == 2
    assert [s.generation for s in trajectory.snapshots] == [0, 1]


def test_to_dict_is_plain_json_serializable_structure() -> None:
    import json

    trajectory = Trajectory()
    trajectory.append(make_snapshot(0))
    encoded = json.dumps(trajectory.to_dict())
    decoded = json.loads(encoded)
    assert decoded[0]["generation"] == 0
    assert decoded[0]["fitness_summary"]["mean"] == 1.0
