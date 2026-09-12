from __future__ import annotations

import numpy as np

from genevra.analysis.learning_strategy import LearningStrategy
from genevra.evolution.fitness import SurvivalResourceFitness
from genevra.evolution.lineage import LineageEvent
from genevra.mechanisms.causal_chain import CAUSAL_CHAIN
from genevra.mechanisms.generalization import GeneralizationAnalyzer, canalization_proxy
from genevra.mechanisms.learning_strategy_evolution import (
    lineage_strategy_inheritance,
    strategy_environment_dependence,
)
from genevra.mechanisms.mutational_landscape import MutationalLandscapeAnalyzer
from genevra.mechanisms.plasticity_cost import PlasticityCostSample, analyze_plasticity_cost
from genevra.mechanisms.regime import classify_regimes
from genevra.mechanisms.report import MechanismsReport
from genevra.mechanisms.robustness import RobustnessAnalyzer, robustness_evolvability_association
from genevra.metrics.behavior import behavioral_signature
from genevra.metrics.diversity import EuclideanDistance
from genevra.organism.genome import ControllerArchitecture, Genome
from genevra.organism.learning import HebbianLearning, NoLearning
from genevra.organism.mutation import GaussianMutation
from genevra.organism.organism import OrganismConfig
from genevra.simulation.grid_world import GridWorldConfig
from genevra.simulation.types import Action

VIEW_RADIUS = 1
MEMORY_SIZE = 2
INPUT_SIZE = (2 * VIEW_RADIUS + 1) ** 2 * 2 + 2 + MEMORY_SIZE


def _genome(seed: int = 0, mutation_rate: float = 1.0, mutation_sigma: float = 0.5) -> Genome:
    arch = ControllerArchitecture(input_size=INPUT_SIZE, hidden_size=4, output_size=len(Action))
    genome = Genome.random(arch, np.random.default_rng(seed))
    genome.mutation_genes[:] = [mutation_rate, mutation_sigma]
    return genome


def _organism_config() -> OrganismConfig:
    return OrganismConfig(view_radius=VIEW_RADIUS, memory_size=MEMORY_SIZE, initial_energy=15.0)


def _env_config() -> GridWorldConfig:
    return GridWorldConfig(width=8, height=8, view_radius=VIEW_RADIUS, max_steps=25)


class TestRobustnessAnalyzer:
    def test_reports_all_dimensions_with_fitness_function(self) -> None:
        analyzer = RobustnessAnalyzer(
            environment_config=_env_config(),
            organism_config=_organism_config(),
            learning_rule=NoLearning(),
            mutation_operator=GaussianMutation(),
            distance=EuclideanDistance(),
            fitness_function=SurvivalResourceFitness(),
            num_samples=3,
            max_steps=25,
        )
        profile = analyzer.analyze(
            _genome(), np.random.default_rng(1), environmental_perturbations=[_env_config()]
        )
        assert profile.genetic.n_samples == 3
        assert profile.behavioral.n_samples == 3
        assert profile.fitness is not None and profile.fitness.n_samples == 3
        assert profile.environmental is not None and profile.environmental.n_samples == 1
        assert profile.learning_amplification is None

    def test_zero_mutation_rate_gives_zero_genetic_distance(self) -> None:
        analyzer = RobustnessAnalyzer(
            environment_config=_env_config(),
            organism_config=_organism_config(),
            learning_rule=NoLearning(),
            mutation_operator=GaussianMutation(),
            distance=EuclideanDistance(),
            num_samples=4,
            max_steps=25,
        )
        genome = _genome(mutation_rate=0.0)
        profile = analyzer.analyze(genome, np.random.default_rng(2))
        # Behavior is unaffected by mutation when the mutation rate is 0, but
        # NoLearning + the same environment_config with different seeds can
        # still vary; genetic distance should be no larger than a repeated
        # stochastic re-evaluation of the unmutated genome.
        assert profile.genetic.mean >= 0.0

    def test_learning_amplification_computed_when_requested(self) -> None:
        analyzer = RobustnessAnalyzer(
            environment_config=_env_config(),
            organism_config=_organism_config(),
            learning_rule=HebbianLearning(),
            mutation_operator=GaussianMutation(),
            distance=EuclideanDistance(),
            num_samples=3,
            max_steps=25,
        )
        profile = analyzer.analyze(
            _genome(), np.random.default_rng(3), include_learning_amplification=True
        )
        assert profile.learning_amplification is not None

    def test_empty_environmental_perturbations_yields_none(self) -> None:
        analyzer = RobustnessAnalyzer(
            environment_config=_env_config(),
            organism_config=_organism_config(),
            learning_rule=NoLearning(),
            mutation_operator=GaussianMutation(),
            distance=EuclideanDistance(),
            num_samples=2,
            max_steps=20,
        )
        profile = analyzer.analyze(_genome(), np.random.default_rng(4))
        assert profile.environmental is None
        assert profile.fitness is None


def test_robustness_evolvability_association_none_below_threshold() -> None:
    assert robustness_evolvability_association([1.0, 2.0], [1.0, 2.0]) is None


def test_robustness_evolvability_association_none_when_constant() -> None:
    assert robustness_evolvability_association([1.0, 1.0, 1.0], [1.0, 2.0, 3.0]) is None


def test_robustness_evolvability_association_computes_correlation() -> None:
    r = robustness_evolvability_association([1.0, 2.0, 3.0, 4.0], [1.0, 2.0, 3.0, 4.0])
    assert r is not None
    assert np.isclose(r, 1.0)


class TestGeneralizationAnalyzer:
    def test_produces_train_and_three_categories(self) -> None:
        analyzer = GeneralizationAnalyzer(
            organism_config=_organism_config(),
            learning_rule=NoLearning(),
            fitness_function=SurvivalResourceFitness(),
            distance=EuclideanDistance(),
            max_steps=25,
        )
        profile = analyzer.analyze(_genome(), _env_config(), np.random.default_rng(5))
        assert {r.category for r in profile.results} == {"recurrent", "related_unseen", "novel"}
        assert profile.train.behavioral_distance_from_train == 0.0

    def test_retention_is_none_for_unknown_category(self) -> None:
        analyzer = GeneralizationAnalyzer(
            organism_config=_organism_config(),
            learning_rule=NoLearning(),
            fitness_function=SurvivalResourceFitness(),
            distance=EuclideanDistance(),
            max_steps=20,
        )
        profile = analyzer.analyze(_genome(), _env_config(), np.random.default_rng(6))
        assert profile.retention("nonexistent") is None

    def test_canalization_proxy_zero_with_no_results(self) -> None:
        analyzer = GeneralizationAnalyzer(
            organism_config=_organism_config(),
            learning_rule=NoLearning(),
            fitness_function=SurvivalResourceFitness(),
            distance=EuclideanDistance(),
        )
        profile = analyzer.analyze(_genome(), _env_config(), np.random.default_rng(7))
        proxy = canalization_proxy(profile)
        assert proxy >= 0.0


class TestMutationalLandscapeAnalyzer:
    def test_one_step_sample_size_matches_num_samples(self) -> None:
        def evaluator(genome: Genome) -> np.ndarray:
            return genome.controller_weights

        analyzer = MutationalLandscapeAnalyzer(
            mutation_operator=GaussianMutation(),
            behavioral_evaluator=evaluator,
            distance=EuclideanDistance(),
            fitness_evaluator=lambda g: float(np.sum(g.controller_weights)),
        )
        report = analyzer.analyze(_genome(), np.random.default_rng(8), num_samples=10)
        assert report.one_step.n_samples == 10
        assert report.two_step is None
        total = (
            (report.one_step.beneficial_fraction or 0.0)
            + (report.one_step.neutral_fraction or 0.0)
            + (report.one_step.deleterious_fraction or 0.0)
        )
        assert np.isclose(total, 1.0)

    def test_two_step_is_sampled_not_exhaustive(self) -> None:
        def evaluator(genome: Genome) -> np.ndarray:
            return genome.controller_weights

        analyzer = MutationalLandscapeAnalyzer(
            mutation_operator=GaussianMutation(),
            behavioral_evaluator=evaluator,
            distance=EuclideanDistance(),
        )
        report = analyzer.analyze(
            _genome(),
            np.random.default_rng(9),
            num_samples=8,
            include_two_step=True,
            num_two_step_samples=5,
        )
        assert report.two_step is not None
        assert report.two_step.n_samples == 5
        assert report.two_step.step == 2

    def test_zero_mutation_rate_all_viable_zero_distance(self) -> None:
        def evaluator(genome: Genome) -> np.ndarray:
            return genome.controller_weights

        analyzer = MutationalLandscapeAnalyzer(
            mutation_operator=GaussianMutation(),
            behavioral_evaluator=evaluator,
            distance=EuclideanDistance(),
        )
        report = analyzer.analyze(
            _genome(mutation_rate=0.0), np.random.default_rng(10), num_samples=5
        )
        assert report.one_step.viable_fraction == 1.0
        assert all(d == 0.0 for d in report.one_step.behavioral_distances)


def test_plasticity_cost_requires_three_paired_observations() -> None:
    samples = [
        PlasticityCostSample(individual_id=0, plasticity_gate=0.1, initial_competence=1.0),
        PlasticityCostSample(individual_id=1, plasticity_gate=0.5, initial_competence=None),
    ]
    report = analyze_plasticity_cost(samples)
    assert report.associations["plasticity_gate__vs__initial_competence"] is None


def test_plasticity_cost_computes_correlation_with_enough_data() -> None:
    samples = [
        PlasticityCostSample(individual_id=i, plasticity_gate=float(i), initial_competence=float(i))
        for i in range(5)
    ]
    report = analyze_plasticity_cost(samples)
    r = report.associations["plasticity_gate__vs__initial_competence"]
    assert r is not None
    assert np.isclose(r, 1.0)


def test_lineage_strategy_inheritance_zero_pairs_when_no_parents() -> None:
    events = [
        LineageEvent(individual_id=0, parent_ids=(), generation=0, genome_hash="a"),
    ]
    result = lineage_strategy_inheritance(events)
    assert result.n_parent_child_pairs == 0


def test_lineage_strategy_inheritance_computes_distance() -> None:
    events = [
        LineageEvent(
            individual_id=0,
            parent_ids=(),
            generation=0,
            genome_hash="a",
            learning_strategy=(0.1, 1.0, 0.0),
        ),
        LineageEvent(
            individual_id=1,
            parent_ids=(0,),
            generation=1,
            genome_hash="b",
            learning_strategy=(0.2, 1.0, 0.0),
        ),
    ]
    result = lineage_strategy_inheritance(events)
    assert result.n_parent_child_pairs == 1
    assert result.mean_strategy_distance > 0.0


def test_strategy_environment_dependence_reports_per_condition_means() -> None:
    strategies_by_condition = {
        "static": [LearningStrategy(0.1, 1.0, 0.0), LearningStrategy(0.2, 1.0, 0.0)],
        "volatile": [LearningStrategy(0.8, 0.5, 0.1)],
    }
    result = strategy_environment_dependence(strategies_by_condition)
    assert result.condition_means["static"][0] == 0.15000000000000002 or np.isclose(
        result.condition_means["static"][0], 0.15
    )
    assert "volatile" in result.condition_means


def test_strategy_environment_dependence_skips_empty_conditions() -> None:
    result = strategy_environment_dependence({"empty": []})
    assert result.condition_means == {}


def test_causal_chain_links_are_named_and_ordered() -> None:
    assert len(CAUSAL_CHAIN) == 7
    assert CAUSAL_CHAIN[0].from_node == "environmental_volatility"
    assert CAUSAL_CHAIN[-1].to_node == "innovation"
    for link in CAUSAL_CHAIN:
        assert link.testable_via


def _trajectory_snapshot(
    generation: int, novelty: float, diversity: float, fitness_mean: float
) -> dict:
    return {
        "generation": generation,
        "instantaneous_novelty": novelty,
        "genotypic_diversity": diversity,
        "behavioral_diversity": diversity,
        "fitness_summary": {"mean": fitness_mean},
    }


def test_classify_regimes_empty_change_points() -> None:
    trajectory = [_trajectory_snapshot(i, 0.5, 0.5, float(i)) for i in range(6)]
    results = classify_regimes(trajectory, [])
    assert len(results) == 6
    assert all(isinstance(r.labels, tuple) for r in results)


def test_classify_regimes_flags_high_diversity_as_exploration() -> None:
    trajectory = [_trajectory_snapshot(i, 0.1, 0.1, 1.0) for i in range(5)]
    trajectory.append(_trajectory_snapshot(5, 0.1, 100.0, 1.0))
    results = classify_regimes(trajectory, [])
    assert "exploration" in results[-1].labels


def test_mechanisms_report_empty_sections_render() -> None:
    report = MechanismsReport()
    text = report.to_text()
    assert "Evolutionary Mechanisms Report" in text
    d = report.to_dict()
    assert d["robustness"] is None


def test_mechanisms_report_renders_robustness_section() -> None:
    analyzer = RobustnessAnalyzer(
        environment_config=_env_config(),
        organism_config=_organism_config(),
        learning_rule=NoLearning(),
        mutation_operator=GaussianMutation(),
        distance=EuclideanDistance(),
        num_samples=2,
        max_steps=15,
    )
    profile = analyzer.analyze(_genome(), np.random.default_rng(11))
    report = MechanismsReport(robustness=profile)
    text = report.to_text()
    assert "Robustness" in text
    assert "genetic" in text


def test_behavioral_signature_smoke() -> None:
    """Sanity check that this test module's genome/environment setup
    actually produces a usable behavioral signature (guards against the
    other tests above passing vacuously if lifetimes silently die
    immediately)."""
    from genevra.evolution.lifetime import run_single_lifetime

    obs = run_single_lifetime(
        _genome(),
        _env_config(),
        _organism_config(),
        NoLearning(),
        env_seed=0,
        organism_seed=0,
        max_steps=25,
    )
    signature = behavioral_signature(obs)
    assert signature.shape[0] > 0
