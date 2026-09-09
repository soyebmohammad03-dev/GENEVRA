from genevra.utils.seeding import seed_everything


def test_same_seed_produces_identical_sequences() -> None:
    rng_a = seed_everything(42)
    rng_b = seed_everything(42)
    assert rng_a.random(10).tolist() == rng_b.random(10).tolist()


def test_different_seeds_produce_different_sequences() -> None:
    rng_a = seed_everything(1)
    rng_b = seed_everything(2)
    assert rng_a.random(10).tolist() != rng_b.random(10).tolist()
