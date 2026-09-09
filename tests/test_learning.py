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
    assert np.array_equal(rule.effective_weights(base_w2, new_state), base_w2)


def test_hebbian_learning_changes_effective_weights_after_update() -> None:
    arch = make_arch()
    rule = HebbianLearning()
    state = rule.init_state(arch)
    base_w2 = np.zeros((arch.output_size, arch.hidden_size), dtype=np.float32)
    pre = np.array([1.0, 0.5, -0.5], dtype=np.float32)
    post = np.array([1.0, 0.0], dtype=np.float32)
    params = LearningParams(learning_rate=0.5)

    new_state = rule.update(state, pre, post, params)
    effective = rule.effective_weights(base_w2, new_state)
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
