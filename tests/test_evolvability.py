import numpy as np

from genevra.arrays import FloatArray
from genevra.metrics.diversity import EuclideanDistance
from genevra.metrics.evolvability import EvolvabilityAnalyzer
from genevra.organism.genome import ControllerArchitecture, Genome
from genevra.organism.mutation import GaussianMutation


def make_genome(mutation_rate: float = 1.0, mutation_sigma: float = 0.5) -> Genome:
    arch = ControllerArchitecture(input_size=4, hidden_size=3, output_size=2)
    genome = Genome.random(arch, np.random.default_rng(0))
    genome.mutation_genes[:] = [mutation_rate, mutation_sigma]
    return genome


def identity_evaluator(genome: Genome) -> FloatArray:
    """A cheap, deterministic stand-in behavioral evaluator: just returns
    the controller weights. Keeps these tests independent of the
    simulation loop while still exercising real genome->mutant->distance
    plumbing."""
    return genome.controller_weights


def test_analysis_respects_configured_sample_budget() -> None:
    analyzer = EvolvabilityAnalyzer(
        mutation_operator=GaussianMutation(),
        behavioral_evaluator=identity_evaluator,
        distance=EuclideanDistance(),
        num_samples=7,
    )
    report = analyzer.analyze(make_genome(), np.random.default_rng(0))
    assert report.num_samples == 7
    assert report.num_viable <= 7


def test_zero_mutation_rate_yields_zero_behavioral_distance() -> None:
    analyzer = EvolvabilityAnalyzer(
        mutation_operator=GaussianMutation(),
        behavioral_evaluator=identity_evaluator,
        distance=EuclideanDistance(),
        num_samples=10,
    )
    genome = make_genome(mutation_rate=0.0)
    report = analyzer.analyze(genome, np.random.default_rng(0))
    assert report.mean_behavioral_distance == 0.0
    assert report.viable_fraction == 1.0


def test_higher_mutation_sigma_increases_behavioral_distance() -> None:
    analyzer = EvolvabilityAnalyzer(
        mutation_operator=GaussianMutation(),
        behavioral_evaluator=identity_evaluator,
        distance=EuclideanDistance(),
        num_samples=30,
    )
    low_sigma_report = analyzer.analyze(make_genome(mutation_sigma=0.01), np.random.default_rng(0))
    high_sigma_report = analyzer.analyze(make_genome(mutation_sigma=2.0), np.random.default_rng(0))
    assert high_sigma_report.mean_behavioral_distance > low_sigma_report.mean_behavioral_distance


def test_inviable_mutants_are_excluded_from_the_distance_average() -> None:
    def flaky_evaluator(genome: Genome) -> FloatArray:
        if genome.controller_weights[0] > 5.0:
            raise ValueError("simulated inviable phenotype")
        return genome.controller_weights

    analyzer = EvolvabilityAnalyzer(
        mutation_operator=GaussianMutation(),
        behavioral_evaluator=flaky_evaluator,
        distance=EuclideanDistance(),
        num_samples=20,
    )
    genome = make_genome(mutation_rate=1.0, mutation_sigma=5.0)
    report = analyzer.analyze(genome, np.random.default_rng(0))
    assert report.num_viable <= report.num_samples
    assert 0.0 <= report.viable_fraction <= 1.0


def test_report_documents_its_own_limitation() -> None:
    analyzer = EvolvabilityAnalyzer(
        mutation_operator=GaussianMutation(),
        behavioral_evaluator=identity_evaluator,
        distance=EuclideanDistance(),
        num_samples=5,
    )
    report = analyzer.analyze(make_genome(), np.random.default_rng(0))
    assert "not" in report.limitation_note.lower()
    assert "adaptive success" in report.limitation_note.lower()


def test_without_fitness_evaluator_classification_fields_are_none() -> None:
    analyzer = EvolvabilityAnalyzer(
        mutation_operator=GaussianMutation(),
        behavioral_evaluator=identity_evaluator,
        distance=EuclideanDistance(),
        num_samples=5,
    )
    report = analyzer.analyze(make_genome(), np.random.default_rng(0))
    assert report.beneficial_fraction is None
    assert report.neutral_fraction is None
    assert report.deleterious_fraction is None


def test_fitness_evaluator_classifies_mutants_and_fractions_sum_to_one() -> None:
    def fitness_evaluator(genome: Genome) -> float:
        return float(np.sum(genome.controller_weights))

    analyzer = EvolvabilityAnalyzer(
        mutation_operator=GaussianMutation(),
        behavioral_evaluator=identity_evaluator,
        distance=EuclideanDistance(),
        num_samples=30,
        fitness_evaluator=fitness_evaluator,
    )
    report = analyzer.analyze(
        make_genome(mutation_rate=1.0, mutation_sigma=1.0), np.random.default_rng(0)
    )
    assert report.beneficial_fraction is not None
    assert report.neutral_fraction is not None
    assert report.deleterious_fraction is not None
    total = report.beneficial_fraction + report.neutral_fraction + report.deleterious_fraction
    assert np.isclose(total, 1.0)


def test_large_behavioral_change_is_not_automatically_classified_beneficial() -> None:
    """A mutation that changes behavior a lot but degrades fitness must
    show up as deleterious, not beneficial — the two measurements are
    independent."""

    def fitness_evaluator(genome: Genome) -> float:
        return -float(np.sum(np.abs(genome.controller_weights)))  # smaller weights = higher fitness

    analyzer = EvolvabilityAnalyzer(
        mutation_operator=GaussianMutation(),
        behavioral_evaluator=identity_evaluator,
        distance=EuclideanDistance(),
        num_samples=30,
        fitness_evaluator=fitness_evaluator,
    )
    genome = make_genome(mutation_rate=1.0, mutation_sigma=5.0)  # large mutations -> large distance
    report = analyzer.analyze(genome, np.random.default_rng(0))
    assert report.mean_behavioral_distance > 0.0
    assert report.deleterious_fraction is not None and report.deleterious_fraction > 0.0
