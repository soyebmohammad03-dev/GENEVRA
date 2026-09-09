import numpy as np

from genevra.analysis.evolvability_over_time import (
    LineageSampling,
    RandomSampling,
    TopScoreSampling,
    sample_evolvability_over_generations,
)
from genevra.evolution.engine import EvolutionConfig, EvolutionEngine
from genevra.evolution.fitness import SurvivalResourceFitness
from genevra.evolution.lineage import LineageTracker
from genevra.evolution.population import PopulationConfig
from genevra.evolution.reproduction import PopulationReproductionConfig
from genevra.evolution.selection import TournamentSelection
from genevra.metrics.diversity import EuclideanDistance
from genevra.metrics.evolvability import EvolvabilityAnalyzer
from genevra.organism.genome import ControllerArchitecture, Genome
from genevra.organism.learning import NoLearning
from genevra.organism.mutation import GaussianMutation
from genevra.organism.organism import OrganismConfig
from genevra.simulation.grid_world import GridWorldConfig
from genevra.simulation.types import Action

_VIEW_RADIUS = 1
_MEMORY_SIZE = 2
_INPUT_SIZE = (2 * _VIEW_RADIUS + 1) ** 2 * 2 + 2 + _MEMORY_SIZE


def make_engine(generations: int = 5) -> EvolutionEngine:
    architecture = ControllerArchitecture(
        input_size=_INPUT_SIZE, hidden_size=5, output_size=len(Action)
    )
    organism_config = OrganismConfig(
        view_radius=_VIEW_RADIUS, memory_size=_MEMORY_SIZE, initial_energy=15.0
    )
    population_config = PopulationConfig(
        size=6, architecture=architecture, organism_config=organism_config
    )
    environment_config = GridWorldConfig(width=8, height=8, view_radius=_VIEW_RADIUS, max_steps=15)
    config = EvolutionConfig(
        generations=generations,
        steps_per_lifetime=15,
        environment_config=environment_config,
        population_config=population_config,
        fitness_function=SurvivalResourceFitness(),
        selection_strategy=TournamentSelection(tournament_size=2),
        reproduction=PopulationReproductionConfig(
            energy_threshold=-1000.0, mutation_operator=GaussianMutation()
        ),
        learning_rule_factory=NoLearning,
        seed=0,
    )
    return EvolutionEngine(config)


def identity_evaluator(genome: Genome):
    return genome.controller_weights


def test_random_sampling_returns_requested_count() -> None:
    genomes = {
        i: Genome.random(ControllerArchitecture(4, 3, 2), np.random.default_rng(i))
        for i in range(10)
    }
    strategy = RandomSampling()
    chosen = strategy.select(genomes, k=3, rng=np.random.default_rng(0))
    assert len(chosen) == 3
    assert len(set(chosen)) == 3


def test_top_score_sampling_picks_highest_scores() -> None:
    genomes = {
        i: Genome.random(ControllerArchitecture(4, 3, 2), np.random.default_rng(i))
        for i in range(5)
    }
    scores = {0: 1.0, 1: 5.0, 2: 3.0, 3: 4.0, 4: 2.0}

    def score_by_id(genome: Genome) -> float:
        for gid, g in genomes.items():
            if g is genome:
                return scores[gid]
        return 0.0

    strategy = TopScoreSampling(score_fn=score_by_id)
    chosen = strategy.select(genomes, k=2, rng=np.random.default_rng(0))
    assert set(chosen) == {1, 3}


def test_lineage_sampling_picks_one_per_founder() -> None:
    tracker = LineageTracker()
    genomes = {}
    for i in range(6):
        genome = Genome.random(ControllerArchitecture(4, 3, 2), np.random.default_rng(i))
        genomes[i] = genome
        parent_ids = (i - 2,) if i >= 2 else ()
        tracker.record_birth(i, parent_ids, generation=i, genome=genome)
    strategy = LineageSampling(tracker)
    chosen = strategy.select(genomes, k=10, rng=np.random.default_rng(0))
    # individuals 0,1 are their own founders; 2,3 descend from 0,1 respectively; etc.
    assert len(chosen) == 2


def test_sample_evolvability_over_generations_respects_requested_generations() -> None:
    engine = make_engine(generations=6)
    analyzer = EvolvabilityAnalyzer(
        mutation_operator=GaussianMutation(),
        behavioral_evaluator=identity_evaluator,
        distance=EuclideanDistance(),
        num_samples=3,
    )
    samples = sample_evolvability_over_generations(
        engine,
        target_generations={0, 2, 4},
        strategy=RandomSampling(),
        analyzer=analyzer,
        samples_per_generation=2,
        rng=np.random.default_rng(0),
    )
    generations_sampled = {s.generation for s in samples}
    assert generations_sampled == {0, 2, 4}
    for sample in samples:
        assert sample.report.num_samples == 3


def test_sample_evolvability_returns_empty_for_no_target_generations() -> None:
    engine = make_engine(generations=3)
    analyzer = EvolvabilityAnalyzer(
        mutation_operator=GaussianMutation(),
        behavioral_evaluator=identity_evaluator,
        distance=EuclideanDistance(),
        num_samples=2,
    )
    samples = sample_evolvability_over_generations(
        engine,
        set(),
        RandomSampling(),
        analyzer,
        samples_per_generation=1,
        rng=np.random.default_rng(0),
    )
    assert samples == []
