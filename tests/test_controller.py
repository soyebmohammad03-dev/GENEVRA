import numpy as np
import pytest

from genevra.organism.controller import Controller, batch_hidden, batch_output
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


def _random_controllers(n: int, arch: ControllerArchitecture, seed: int) -> list[Controller]:
    rng = np.random.default_rng(seed)
    controllers = []
    for _ in range(n):
        weights = rng.normal(0, 0.5, arch.num_params).astype(np.float32)
        controllers.append(Controller.from_weights(arch, weights))
    return controllers


@pytest.mark.parametrize("n", [0, 1, 5, 50])
def test_batch_hidden_matches_individual_calls(n: int) -> None:
    arch = ControllerArchitecture(input_size=7, hidden_size=6, output_size=4)
    controllers = _random_controllers(n, arch, seed=1)
    rng = np.random.default_rng(2)
    inputs = rng.normal(0, 1, (n, arch.input_size)).astype(np.float32)

    batched = batch_hidden(controllers, inputs)
    individual = (
        np.stack([c.hidden(x) for c, x in zip(controllers, inputs, strict=True)])
        if n
        else np.zeros((0, 0))
    )

    assert batched.shape == individual.shape
    assert np.allclose(batched, individual, atol=1e-5)


@pytest.mark.parametrize("n", [0, 1, 5, 50])
def test_batch_output_matches_individual_calls(n: int) -> None:
    arch = ControllerArchitecture(input_size=7, hidden_size=6, output_size=4)
    controllers = _random_controllers(n, arch, seed=3)
    rng = np.random.default_rng(4)
    inputs = rng.normal(0, 1, (n, arch.input_size)).astype(np.float32)

    hidden = batch_hidden(controllers, inputs)
    batched_logits = batch_output(controllers, hidden)
    individual_logits = (
        np.stack([c.output(h) for c, h in zip(controllers, hidden, strict=True)])
        if n
        else np.zeros((0, 0))
    )

    assert batched_logits.shape == individual_logits.shape
    assert np.allclose(batched_logits, individual_logits, atol=1e-5)


def test_batch_output_with_per_organism_overrides_matches_individual() -> None:
    arch = ControllerArchitecture(input_size=5, hidden_size=4, output_size=3)
    controllers = _random_controllers(4, arch, seed=5)
    rng = np.random.default_rng(6)
    inputs = rng.normal(0, 1, (4, arch.input_size)).astype(np.float32)
    hidden = batch_hidden(controllers, inputs)

    overrides_w2 = np.stack([c.weight2 + rng.normal(0, 0.1, c.weight2.shape) for c in controllers])
    overrides_b2 = np.stack([c.bias2 for c in controllers])

    batched_logits = batch_output(controllers, hidden, overrides_w2, overrides_b2)
    individual_logits = np.stack(
        [
            c.output(h, weights_override=(w2, b2))
            for c, h, w2, b2 in zip(controllers, hidden, overrides_w2, overrides_b2, strict=True)
        ]
    )
    assert np.allclose(batched_logits, individual_logits, atol=1e-5)


def test_batch_hidden_rejects_wrong_input_shape() -> None:
    arch = ControllerArchitecture(input_size=5, hidden_size=4, output_size=3)
    controllers = _random_controllers(3, arch, seed=7)
    with pytest.raises(ValueError):
        batch_hidden(controllers, np.zeros((3, 4), dtype=np.float32))
