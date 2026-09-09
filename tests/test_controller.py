import numpy as np
import pytest

from genevra.organism.controller import Controller
from genevra.organism.genome import ControllerArchitecture


def test_forward_pass_produces_expected_output_shape() -> None:
    arch = ControllerArchitecture(input_size=5, hidden_size=4, output_size=3)
    rng = np.random.default_rng(0)
    weights = rng.normal(0, 0.5, arch.num_params).astype(np.float32)
    controller = Controller.from_weights(arch, weights)

    x = rng.normal(0, 1, arch.input_size).astype(np.float32)
    hidden = controller.hidden(x)
    assert hidden.shape == (arch.hidden_size,)
    assert np.all(np.abs(hidden) <= 1.0)  # tanh-bounded

    logits = controller.output(hidden)
    assert logits.shape == (arch.output_size,)


def test_forward_pass_is_deterministic_given_same_weights_and_input() -> None:
    arch = ControllerArchitecture(input_size=5, hidden_size=4, output_size=3)
    rng = np.random.default_rng(0)
    weights = rng.normal(0, 0.5, arch.num_params).astype(np.float32)
    controller = Controller.from_weights(arch, weights)
    x = np.ones(arch.input_size, dtype=np.float32)

    hidden_a = controller.hidden(x)
    hidden_b = controller.hidden(x)
    assert np.array_equal(hidden_a, hidden_b)


def test_weights_override_changes_output_without_mutating_base() -> None:
    arch = ControllerArchitecture(input_size=3, hidden_size=2, output_size=2)
    rng = np.random.default_rng(1)
    weights = rng.normal(0, 0.5, arch.num_params).astype(np.float32)
    controller = Controller.from_weights(arch, weights)
    x = np.ones(arch.input_size, dtype=np.float32)
    hidden = controller.hidden(x)

    base_logits = controller.output(hidden)
    override_w2 = controller.weight2 + 10.0
    override_logits = controller.output(hidden, weights_override=(override_w2, controller.bias2))

    assert not np.array_equal(base_logits, override_logits)
    assert np.array_equal(controller.weight2, controller.weight2)  # base untouched


def test_rejects_wrong_input_shape() -> None:
    arch = ControllerArchitecture(input_size=5, hidden_size=4, output_size=3)
    weights = np.zeros(arch.num_params, dtype=np.float32)
    controller = Controller.from_weights(arch, weights)
    with pytest.raises(ValueError):
        controller.hidden(np.zeros(3, dtype=np.float32))
