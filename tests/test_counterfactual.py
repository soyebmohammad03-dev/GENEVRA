import numpy as np
import pytest

from genevra.analysis.counterfactual import CounterfactualAnalyzer, Perturbation
from genevra.arrays import FloatArray
from genevra.metrics.diversity import EuclideanDistance
from genevra.organism.genome import ControllerArchitecture, Genome


def make_genome() -> Genome:
    arch = ControllerArchitecture(input_size=4, hidden_size=3, output_size=2)
    genome = Genome.random(arch, np.random.default_rng(0))
    genome.learning_genes[:] = [0.1, 0.5, 0.2]
    return genome


def behavioral_evaluator(genome: Genome) -> FloatArray:
    """Deterministic stand-in: behavior is a function of the learning
    genes only, so a perturbation's effect is directly measurable."""
    return genome.learning_genes.astype(np.float64)


def test_perturbation_rejects_unimplemented_gene_names() -> None:
    with pytest.raises(ValueError, match="gene must be one of"):
        Perturbation(gene="exploration_tendency", delta=0.1)


def test_original_genome_is_never_mutated() -> None:
    genome = make_genome()
    original = genome.learning_genes.copy()
    analyzer = CounterfactualAnalyzer(behavioral_evaluator, EuclideanDistance())
    analyzer.analyze(genome, [Perturbation(gene="learning_rate", delta=1.0)])
    assert np.array_equal(genome.learning_genes, original)


def test_larger_perturbation_produces_larger_behavioral_distance() -> None:
    genome = make_genome()
    analyzer = CounterfactualAnalyzer(behavioral_evaluator, EuclideanDistance())
    small, large = analyzer.analyze(
        genome,
        [
            Perturbation(gene="learning_rate", delta=0.01),
            Perturbation(gene="learning_rate", delta=1.0),
        ],
    )
    assert large.behavioral_distance > small.behavioral_distance


def test_fitness_and_novelty_deltas_are_none_without_evaluators() -> None:
    genome = make_genome()
    analyzer = CounterfactualAnalyzer(behavioral_evaluator, EuclideanDistance())
    (result,) = analyzer.analyze(genome, [Perturbation(gene="decay", delta=0.1)])
    assert result.fitness_delta is None
    assert result.novelty_delta is None
    assert result.viable


def test_fitness_evaluator_is_used_when_supplied() -> None:
    genome = make_genome()

    def fitness_evaluator(g: Genome) -> float:
        return float(np.sum(g.learning_genes))

    analyzer = CounterfactualAnalyzer(
        behavioral_evaluator, EuclideanDistance(), fitness_evaluator=fitness_evaluator
    )
    (result,) = analyzer.analyze(genome, [Perturbation(gene="learning_rate", delta=0.5)])
    assert result.fitness_delta is not None
    assert result.fitness_delta == pytest.approx(0.5, abs=1e-6)


def test_inviable_variant_is_reported_not_raised() -> None:
    genome = make_genome()

    def flaky_evaluator(g: Genome) -> FloatArray:
        if g.learning_genes[0] > 0.5:
            raise ValueError("simulated inviable phenotype")
        return g.learning_genes.astype(np.float64)

    analyzer = CounterfactualAnalyzer(flaky_evaluator, EuclideanDistance())
    (result,) = analyzer.analyze(genome, [Perturbation(gene="learning_rate", delta=10.0)])
    assert result.viable is False


def test_mechanism_and_outcome_are_kept_as_separate_fields() -> None:
    genome = make_genome()
    analyzer = CounterfactualAnalyzer(behavioral_evaluator, EuclideanDistance())
    (result,) = analyzer.analyze(genome, [Perturbation(gene="plasticity_gate", delta=-0.1)])
    assert result.mechanism.gene == "plasticity_gate"
    assert "not" in result.limitation_note.lower()
    assert "causal" in result.limitation_note.lower()
