import numpy as np

from genevra.analysis.learning_strategy import (
    LearningStrategy,
    WeightedStrategyDistance,
    learning_strategy_diversity,
    strategies_from_genomes,
)
from genevra.organism.genome import ControllerArchitecture, Genome


def make_genome(learning_genes: tuple[float, float, float]) -> Genome:
    arch = ControllerArchitecture(input_size=4, hidden_size=3, output_size=2)
    genome = Genome.random(arch, np.random.default_rng(0))
    genome.learning_genes[:] = learning_genes
    return genome


def test_strategy_extraction_is_independent_of_controller_weights() -> None:
    genome_a = make_genome((0.1, 0.5, 0.2))
    genome_b = make_genome((0.1, 0.5, 0.2))
    genome_b.controller_weights[:] = genome_b.controller_weights + 999.0

    strategy_a = LearningStrategy.from_genome(genome_a)
    strategy_b = LearningStrategy.from_genome(genome_b)
    assert strategy_a == strategy_b


def test_strategy_extraction_clips_plasticity_gate_and_decay() -> None:
    strategy = LearningStrategy.from_genome(make_genome((0.1, 5.0, -3.0)))
    assert strategy.plasticity_gate == 1.0
    assert strategy.decay == 0.0


def test_distance_is_zero_for_identical_strategies() -> None:
    strategy = LearningStrategy(learning_rate=0.1, plasticity_gate=0.5, decay=0.2)
    distance = WeightedStrategyDistance()
    assert distance.strategy_distance(strategy, strategy) == 0.0


def test_distance_ignores_zero_weighted_dimensions() -> None:
    a = LearningStrategy(learning_rate=0.1, plasticity_gate=0.5, decay=0.2)
    b = LearningStrategy(learning_rate=0.9, plasticity_gate=0.5, decay=0.2)
    distance = WeightedStrategyDistance(weights={"learning_rate": 0.0})
    assert distance.strategy_distance(a, b) == 0.0


def test_diversity_is_zero_for_a_uniform_population() -> None:
    genomes = [make_genome((0.1, 0.5, 0.2)) for _ in range(5)]
    strategies = strategies_from_genomes(genomes)
    assert learning_strategy_diversity(strategies) == 0.0


def test_diversity_increases_with_spread() -> None:
    uniform = strategies_from_genomes([make_genome((0.1, 0.5, 0.2)) for _ in range(5)])
    spread = strategies_from_genomes(
        [make_genome((rate, 0.5, 0.2)) for rate in (0.0, 0.2, 0.4, 0.6, 0.8)]
    )
    assert learning_strategy_diversity(spread) > learning_strategy_diversity(uniform)
