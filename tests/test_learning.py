import numpy as np

from genevra.organism.genome import ControllerArchitecture
from genevra.organism.learning import HebbianLearning, LearningParams, NoLearning


def make_arch() -> ControllerArchitecture:
    return ControllerArchitecture(input_size=4, hidden_size=3, output_size=2)


def test_no_learning_never_changes_effective_weights() -> None:
    arch = make_arch()
    rule = NoLearning()
    state = rule.init_state(arch)
    base_w2 = np.ones((arch.output_size, arch.hidden_size), dtype=np.float32)
    pre = np.array([1.0, 0.5, -0.5], dtype=np.float32)
    post = np.array([1.0, 0.0], dtype=np.float32)
    params = LearningParams(learning_rate=0.5)

    new_state = rule.update(state, pre, post, params)
    assert np.array_equal(rule.effective_weights(base_w2, new_state, params), base_w2)


def test_hebbian_learning_changes_effective_weights_after_update() -> None:
    arch = make_arch()
    rule = HebbianLearning()
    state = rule.init_state(arch)
    base_w2 = np.zeros((arch.output_size, arch.hidden_size), dtype=np.float32)
    pre = np.array([1.0, 0.5, -0.5], dtype=np.float32)
    post = np.array([1.0, 0.0], dtype=np.float32)
    params = LearningParams(learning_rate=0.5)

    new_state = rule.update(state, pre, post, params)
    effective = rule.effective_weights(base_w2, new_state, params)
    assert not np.array_equal(effective, base_w2)


def test_hebbian_delta_is_lifetime_state_not_written_into_base_weights() -> None:
    """The learned delta must live in LearningState, never mutate the
    inherited base weight matrix passed in."""
    arch = make_arch()
    rule = HebbianLearning()
    state = rule.init_state(arch)
    base_w2 = np.zeros((arch.output_size, arch.hidden_size), dtype=np.float32)
    original_base = base_w2.copy()
    pre = np.array([1.0, 0.5, -0.5], dtype=np.float32)
    post = np.array([1.0, 0.0], dtype=np.float32)
    params = LearningParams(learning_rate=0.5)

    rule.update(state, pre, post, params)
    assert np.array_equal(base_w2, original_base)


def test_learning_rate_controls_magnitude_of_change() -> None:
    """learning_rate (C: heritable control of HOW learning happens) must
    actually change the resulting plastic delta."""
    arch = make_arch()
    rule = HebbianLearning()
    pre = np.array([1.0, 0.5, -0.5], dtype=np.float32)
    post = np.array([1.0, 0.0], dtype=np.float32)

    small_lr_state = rule.update(
        rule.init_state(arch), pre, post, LearningParams(learning_rate=0.01)
    )
    large_lr_state = rule.update(
        rule.init_state(arch), pre, post, LearningParams(learning_rate=1.0)
    )

    small_magnitude = np.abs(small_lr_state.output_weight_delta).sum()
    large_magnitude = np.abs(large_lr_state.output_weight_delta).sum()
    assert large_magnitude > small_magnitude


def test_plasticity_gate_scales_effective_weights_independent_of_learning_rate() -> None:
    """A zero gate suppresses the lifetime effect of learning even though
    the plastic delta itself (learning_rate-driven) is unaffected —
    "does this organism use its learning capacity" is a separate
    mechanism from "how fast would it learn if it did."""
    arch = make_arch()
    rule = HebbianLearning()
    base_w2 = np.zeros((arch.output_size, arch.hidden_size), dtype=np.float32)
    pre = np.array([1.0, 0.5, -0.5], dtype=np.float32)
    post = np.array([1.0, 0.0], dtype=np.float32)

    gated_off = LearningParams(learning_rate=0.5, plasticity_gate=0.0)
    state = rule.update(rule.init_state(arch), pre, post, gated_off)
    assert np.array_equal(rule.effective_weights(base_w2, state, gated_off), base_w2)
    assert not np.all(state.output_weight_delta == 0.0)  # the delta itself still accumulated

    gated_on = LearningParams(learning_rate=0.5, plasticity_gate=1.0)
    state_on = rule.update(rule.init_state(arch), pre, post, gated_on)
    assert not np.array_equal(rule.effective_weights(base_w2, state_on, gated_on), base_w2)


def test_decay_bounds_accumulated_plastic_delta_across_repeated_updates() -> None:
    """decay=1.0 means the plastic delta never accumulates past one
    step's contribution; decay=0.0 (default) accumulates without bound
    (up to the HebbianLearning clip)."""
    arch = make_arch()
    rule = HebbianLearning(clip=1000.0)
    pre = np.array([1.0, 0.5, -0.5], dtype=np.float32)
    post = np.array([1.0, 0.0], dtype=np.float32)

    no_decay = LearningParams(learning_rate=0.1, decay=0.0)
    full_decay = LearningParams(learning_rate=0.1, decay=1.0)

    state_no_decay = rule.init_state(arch)
    state_full_decay = rule.init_state(arch)
    for _ in range(5):
        state_no_decay = rule.update(state_no_decay, pre, post, no_decay)
        state_full_decay = rule.update(state_full_decay, pre, post, full_decay)

    accumulated = np.abs(state_no_decay.output_weight_delta).sum()
    non_accumulated = np.abs(state_full_decay.output_weight_delta).sum()
    assert accumulated > non_accumulated
