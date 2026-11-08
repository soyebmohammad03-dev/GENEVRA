"""Hand-calculated and adversarial cases for the GENEVRA reference path."""

import itertools
import math
import runpy
from pathlib import Path

import pytest

REF = runpy.run_path(str(Path(__file__).resolve().parents[1] / "scripts/benchmark_reference.py"))


def test_omission_hull_by_hand():
    assert REF["envelope"](0.1, 0.2, 0.25, 0.5) == pytest.approx((0.075, 0.275))
    assert REF["envelope"](0.1, 0.2, 0.25, 0.05) == pytest.approx((0.075, 0.2))
    assert REF["envelope"](0.2, 0.2, 0.0, 1.0) == (0.2, 0.2)
    assert REF["envelope"](0.0, 1.0, 1.0, 1.0) == (0.0, 1.0)


def test_degenerate_binomial_analytic():
    lo, hi = REF["bernoulli_limits"](0, 10, 0.05)
    assert lo == 0
    assert (1 - hi) ** 10 == pytest.approx(0.05 / 4)
    lo, hi = REF["bernoulli_limits"](10, 10, 0.05)
    assert hi == 1
    assert lo**10 == pytest.approx(0.05 / 4)


def test_balanced_two_trials_by_hand():
    # Under a half success, likelihood relative to its peak is 4p(1-p).
    a, b = REF["bernoulli_limits"](1, 2, 0.2)
    assert a == pytest.approx((1 - math.sqrt(0.95)) / 2)
    assert b == pytest.approx(1 - a)


@pytest.mark.parametrize(
    "k,n,alpha", [(0, 0, 0.05), (2, 1, 0.05), (-1, 2, 0.05), (0, 2, 1), (True, 2, 0.05)]
)
def test_invalid_counts(k, n, alpha):
    with pytest.raises(ValueError):
        REF["bernoulli_limits"](k, n, alpha)


def test_boundary_and_false_certificate():
    exact = REF["classify"](0.6, 0.6, 0.6, 0.6, 0.6, True, 0.3, 0.3)
    assert exact["coverage"] == exact["useful"] == exact["certificate"] == 1
    assert exact["call"] == -1
    assert exact["false_certificate"] == exact["abstention"] == 0
    wrong = REF["classify"](1.0, 1.5, 2.0, 0.6, 0.6, True, 0.31, 0.3)
    assert wrong["coverage"] == wrong["useful"] == wrong["wrong_call"] == 0
    assert wrong["false_certificate"] == 1 and wrong["utility"] == -1


@pytest.mark.parametrize("lo,hi", [(float("nan"), 1), (2, 1), (0, float("inf"))])
def test_invalid_interval(lo, hi):
    with pytest.raises(ValueError):
        REF["classify"](lo, hi, 0.6, 0.6, 0.6, False, 0.0, 0.3)


@pytest.mark.parametrize("budget,tariffs", [(48, (1, 2)), (96, (8, 16)), (60, (1, 1))])
@pytest.mark.parametrize("variance", [None, (0.25, 0.25), (0.0002, 0.038), (0.0, 0.25)])
def test_integer_allocation_agrees_with_exhaustive_grid(budget, tariffs, variance):
    c0, c1 = tariffs
    weights = (0.9, 0.1)

    def loss(units):
        if variance is None:
            return sum(w / math.sqrt(n) for w, n in zip(weights, units, strict=True))
        return sum(w * w * v / n for w, v, n in zip(weights, variance, units, strict=True))

    pairs = [
        (a, b)
        for a, b in itertools.product(range(1, budget // c0 + 1), range(1, budget // c1 + 1))
        if a * c0 + b * c1 == budget
    ]
    high = REF["optimal_high"](budget, tariffs, weights, variance)
    assert loss(((budget - c1 * high) // c0, high)) == pytest.approx(min(map(loss, pairs)))


def test_paired_range_and_multiplicity():
    d = [-1] * 103 + [0] * 153
    ordinary = REF["hoeffding"](d, 0.05, 1)
    corrected = REF["hoeffding"](d, 0.05 / 17, 1)
    assert ordinary[0] == corrected[0] == -103 / 256
    assert ordinary[1:] == pytest.approx([-0.5721064394675774, -0.23258106053242256])
    assert corrected[1] < ordinary[1] < ordinary[2] < corrected[2]
    with pytest.raises(ValueError):
        REF["hoeffding"]([2], 0.05, 1)


def test_exact_safety_edges_and_reference():
    assert REF["binomial_upper"](0, 10, 0.05) == pytest.approx(1 - 0.05**0.1)
    assert REF["binomial_upper"](10, 10, 0.05) == 1
    assert REF["binomial_upper"](180, 512, 0.05 / 9) == pytest.approx(0.40729462357541524)
