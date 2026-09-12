import numpy as np

from genevra.evolution.continuous import ContinuousEvolutionConfig, ContinuousEvolutionEngine
from genevra.evolution.lineage import LineageEvent
from genevra.organism.genome import ControllerArchitecture
from genevra.organism.organism import OrganismConfig
from genevra.population_analysis.aggregation import (
    reduce_within_seed,
    seed_level_values,
    to_condition_sample,
)
from genevra.population_analysis.lineage_ecology import convergent_evolution_check
from genevra.population_analysis.matrix import (
    MatrixMode,
    build_metapopulation_condition,
    build_strategy_ecology_matrix,
    seed_schedule,
)
from genevra.population_analysis.perturbation import (
    evaluate_perturbation_windows,
    run_perturbation_experiment,
)
from genevra.population_analysis.prediction import test_lagged_prediction as run_lagged_prediction
from genevra.population_analysis.prediction import (
    within_seed_lagged_correlation,
)
from genevra.population_analysis.replication_consistency import summarize_replication_consistency
from genevra.population_analysis.robustness_population import (
    PopulationRobustnessAnalyzer,
    robustness_metric_association,
)
from genevra.population_analysis.temporal_validation import (
    leave_one_seed_out,
    within_seed_holdout,
)
from genevra.simulation.shared_grid_world import SharedGridWorldConfig
from genevra.simulation.types import Action

_VIEW_RADIUS = 1
_MEMORY_SIZE = 2
_INPUT_SIZE = (2 * _VIEW_RADIUS + 1) ** 2 * 3 + 2 + _MEMORY_SIZE


def _make_patch_config(seed: int = 0, total_steps: int = 30) -> ContinuousEvolutionConfig:
    architecture = ControllerArchitecture(
        input_size=_INPUT_SIZE, hidden_size=6, output_size=len(Action)
    )
    organism_config = OrganismConfig(
        view_radius=_VIEW_RADIUS, memory_size=_MEMORY_SIZE, initial_energy=15.0, channels=3
    )
    environment_config = SharedGridWorldConfig(
        width=8, height=8, view_radius=_VIEW_RADIUS, max_agents=10, max_steps=10_000
    )
    return ContinuousEvolutionConfig(
        total_steps=total_steps,
        initial_population=6,
        max_population=10,
        environment_config=environment_config,
        architecture=architecture,
        organism_config=organism_config,
        reproduction_energy_threshold=18.0,
        offspring_energy_cost=5.0,
        seed=seed,
        log_every=5,
    )


# --- aggregation ------------------------------------------------------


def test_seed_level_values_reduces_correctly() -> None:
    result = seed_level_values({1: [1.0, 2.0, 3.0], 2: [10.0, 20.0]})
    assert result == {1: 2.0, 2: 15.0}


def test_reduce_within_seed_rejects_empty() -> None:
    try:
        reduce_within_seed([], max)
        raise AssertionError("expected ValueError")
    except ValueError:
        pass


def test_to_condition_sample_is_seed_ordered() -> None:
    assert to_condition_sample({2: 20.0, 1: 10.0}) == [10.0, 20.0]


# --- robustness_population ----------------------------------------------


def test_population_robustness_summary_basic() -> None:
    rng = np.random.default_rng(0)
    summary = PopulationRobustnessAnalyzer().summarize({1: 0.1, 2: 0.2, 3: 0.15}, rng)
    assert summary.n_seeds == 3
    assert summary.mean is not None
    assert summary.bootstrap_ci is not None


def test_population_robustness_summary_empty() -> None:
    rng = np.random.default_rng(0)
    summary = PopulationRobustnessAnalyzer().summarize({}, rng)
    assert summary.n_seeds == 0
    assert summary.mean is None


def test_robustness_metric_association_insufficient_seeds() -> None:
    assert robustness_metric_association({1: 0.1, 2: 0.2}, {1: 0.5, 2: 0.6}) is None


def test_robustness_metric_association_computed() -> None:
    a = {1: 0.1, 2: 0.2, 3: 0.3}
    b = {1: 0.5, 2: 0.6, 3: 0.7}
    r = robustness_metric_association(a, b)
    assert r is not None and r > 0.9


# --- prediction -----------------------------------------------------------


def test_within_seed_lagged_correlation_perfect_relationship() -> None:
    x = [1.0, 2.0, 3.0, 4.0, 5.0]
    y = [0.0, 1.0, 2.0, 3.0, 4.0, 5.0]  # y[t] = x[t-1]
    r = within_seed_lagged_correlation(x, y, lag=1)
    assert r is not None and r > 0.9


def test_lagged_prediction_across_seeds() -> None:
    rng = np.random.default_rng(0)
    predictor = {1: [1.0, 2.0, 3.0, 4.0], 2: [2.0, 3.0, 4.0, 5.0]}
    outcome = {1: [0.0, 1.0, 2.0, 3.0, 4.0], 2: [0.0, 2.0, 3.0, 4.0, 5.0]}
    result = run_lagged_prediction(predictor, outcome, lag=1, rng=rng)
    assert result.n_seeds == 2
    assert result.mean_correlation is not None


# --- temporal_validation ----------------------------------------------


def test_within_seed_holdout_sign_matches_for_monotonic_series() -> None:
    x = list(range(20))
    y = [2.0 * v for v in x]
    result = within_seed_holdout(x, y)
    assert result.train_fit is not None
    assert result.held_out_sign_matches is True


def test_leave_one_seed_out_requires_three_seeds() -> None:
    result = leave_one_seed_out({1: [1.0, 2.0]}, {1: [1.0, 2.0]})
    assert result.agreement_rate is None


def test_leave_one_seed_out_consistent_relationship() -> None:
    x_by_seed = {1: list(range(10)), 2: list(range(10)), 3: list(range(10))}
    y_by_seed = {s: [2.0 * v for v in x_by_seed[s]] for s in x_by_seed}
    result = leave_one_seed_out(x_by_seed, y_by_seed)
    assert result.agreement_rate == 1.0


# --- replication_consistency ---------------------------------------------


def test_replication_consistency_full_agreement() -> None:
    report = summarize_replication_consistency({1: 0.5, 2: 0.3, 3: 0.8})
    assert report.agreement_fraction == 1.0
    assert report.sign_reversals == 0


def test_replication_consistency_sign_reversal() -> None:
    report = summarize_replication_consistency({1: 0.5, 2: -0.3, 3: 0.8})
    assert report.sign_reversals == 1
    assert report.agreement_fraction == 2 / 3


def test_replication_consistency_empty() -> None:
    report = summarize_replication_consistency({})
    assert report.n_seeds == 0
    assert report.agreement_fraction is None


# --- perturbation -----------------------------------------------------


def test_evaluate_perturbation_windows_resistance_and_recovery() -> None:
    before = [10.0, 10.0, 10.0]
    during = [5.0, 4.0, 5.0]
    after = [6.0, 8.0, 9.5]
    result = evaluate_perturbation_windows(before, during, after, recovery_tolerance=0.1)
    assert result.resistance == 6.0
    assert result.recovered is True
    assert result.recovery_step_index == 2


def test_evaluate_perturbation_windows_no_recovery() -> None:
    result = evaluate_perturbation_windows([10.0], [2.0], [3.0], recovery_tolerance=0.1)
    assert result.recovered is False


def test_run_perturbation_experiment_end_to_end() -> None:
    engine = ContinuousEvolutionEngine(_make_patch_config(seed=1))

    def perturb(e: ContinuousEvolutionEngine) -> None:
        e.environment.perturb_resources("A", 0.5, np.random.default_rng(0))

    def metric(e: ContinuousEvolutionEngine) -> float:
        return float(len(e.population))

    result = run_perturbation_experiment(engine, 5, 5, 5, perturb, metric)
    assert len(result.before_values) == 5
    assert len(result.during_values) == 5
    assert len(result.after_values) == 5


# --- matrix -----------------------------------------------------------


def test_build_strategy_ecology_matrix_shape() -> None:
    architecture = ControllerArchitecture(
        input_size=_INPUT_SIZE, hidden_size=6, output_size=len(Action)
    )
    organism_config = OrganismConfig(
        view_radius=_VIEW_RADIUS, memory_size=_MEMORY_SIZE, initial_energy=15.0, channels=3
    )
    matrix = build_strategy_ecology_matrix(architecture, organism_config, MatrixMode.PILOT)
    assert len(matrix) == 4  # 2 learning x 2 single-patch ecology x 1 environment
    config = matrix["no_learning__isolated__static"](seed=0)
    assert config.seed == 0
    assert config.environment_config.max_agents == config.initial_population


def test_build_metapopulation_condition_runs() -> None:
    from genevra.population_analysis.matrix import LearningAxis

    architecture = ControllerArchitecture(
        input_size=_INPUT_SIZE, hidden_size=6, output_size=len(Action)
    )
    organism_config = OrganismConfig(
        view_radius=_VIEW_RADIUS, memory_size=_MEMORY_SIZE, initial_energy=15.0, channels=3
    )
    factory = build_metapopulation_condition(
        architecture, organism_config, MatrixMode.PILOT, LearningAxis.NO_LEARNING
    )
    mp = factory(seed=0)
    history = mp.run(20)
    assert len(history) > 0


def test_seed_schedule_deterministic() -> None:
    assert seed_schedule(MatrixMode.PILOT, base_seed=5) == seed_schedule(
        MatrixMode.PILOT, base_seed=5
    )
    assert len(seed_schedule(MatrixMode.STANDARD)) == 5


# --- lineage_ecology -------------------------------------------------


def _event(
    individual_id: int, parent_ids: tuple[int, ...], strategy: tuple[float, float, float]
) -> LineageEvent:
    return LineageEvent(
        individual_id=individual_id,
        parent_ids=parent_ids,
        generation=0,
        genome_hash="abc",
        learning_strategy=strategy,
    )


def test_convergent_evolution_check_detects_close_independent_strategies() -> None:
    events = [
        _event(0, (), (0.1, 1.0, 0.0)),
        _event(1, (), (0.1, 1.0, 0.0001)),  # independent founder, near-identical strategy
        _event(2, (0,), (5.0, 5.0, 5.0)),  # descendant of 0, far away
    ]
    result = convergent_evolution_check(events, threshold=0.01)
    assert result.n_independent_lineage_pairs_checked == 2  # (0,1) and (1,2)
    assert result.n_convergent_pairs == 1


def test_convergent_evolution_check_no_independent_pairs() -> None:
    events = [_event(0, (), (0.0, 0.0, 0.0))]
    result = convergent_evolution_check(events)
    assert result.n_independent_lineage_pairs_checked == 0
    assert result.convergence_rate is None


# --- Phase 18.18: explicit data-leakage tests -------------------------------
# These construct cases where, IF a held-out seed or held-out generations
# leaked into training, the reported result would differ from what it
# actually is — a passing test here is evidence the safeguard holds, not
# just that the function runs.


def test_leave_one_seed_out_does_not_leak_held_out_seed_into_training() -> None:
    from genevra.population_analysis.temporal_validation import leave_one_seed_out

    # Seeds 0, 1: clean negative relationship. Seed 2 (to be held out): a
    # much larger, opposite-sign relationship. If seed 2's data leaked into
    # its own held-out training fold, the pooled fit would flip positive
    # (dominated by seed 2's magnitude) and *agree* with seed 2's own sign.
    # Without leakage, the fold trained only on {0, 1} stays negative and
    # *disagrees* with seed 2's positive sign.
    x_by_seed = {
        0: [0.0, 1.0, 2.0],
        1: [0.0, 1.0, 2.0],
        2: [0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0],
    }
    y_by_seed = {
        0: [0.0, -1.0, -2.0],
        1: [0.0, -1.0, -2.0],
        2: [0.0, 1000.0, 2000.0, 3000.0, 4000.0, 5000.0, 6000.0, 7000.0, 8000.0, 9000.0],
    }
    result = leave_one_seed_out(x_by_seed, y_by_seed)
    assert result.held_out_sign_matches_by_seed[2] is False

    # Demonstrate what leakage WOULD look like: fitting on all seeds
    # (including the held-out one) flips the fit positive, which WOULD
    # agree with seed 2's own sign — showing the safeguard is load-bearing,
    # not a no-op.
    import numpy as np

    all_x = [v for s in x_by_seed.values() for v in s]
    all_y = [v for s in y_by_seed.values() for v in s]
    leaky_slope = np.polyfit(all_x, all_y, 1)[0]
    assert leaky_slope > 0  # the leaked fit's sign would have agreed with seed 2


def test_within_seed_holdout_future_generations_never_enter_training_fit() -> None:
    from genevra.population_analysis.temporal_validation import within_seed_holdout

    x = list(range(10))
    y_original = [float(i) for i in range(10)]
    y_mutated_future = list(y_original)
    y_mutated_future[5:] = [-999.0] * 5  # rewrite only the held-out half

    result_original = within_seed_holdout(x, y_original, split_fraction=0.5)
    result_mutated = within_seed_holdout(x, y_mutated_future, split_fraction=0.5)

    assert result_original.train_fit is not None
    assert result_mutated.train_fit is not None
    # The train fit must be identical: it only ever saw x[:5]/y[:5], which
    # is unchanged between the two calls.
    assert result_original.train_fit == result_mutated.train_fit
    # But the reported held-out agreement differs, since *that* correctly
    # does depend on the (now-mutated) held-out segment.
    assert result_original.held_out_sign_matches != result_mutated.held_out_sign_matches
