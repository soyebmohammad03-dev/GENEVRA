"""Statistical and acquisition contracts for the coverage-envelope extension."""

from math import comb, sqrt

import numpy as np
import pytest

from genevra.analysis.coverage_envelope import (
    CoverageEnvelope,
    bernoulli_band,
    plan_units,
    reachable_band,
    score_decision,
)


def test_no_missingness_recovers_reachable_band():
    assert CoverageEnvelope((0, 0), (0, 1)).target_tail((0.2, 0.4)) == (0.2, 0.4)


def test_two_worlds_and_mass_cap():
    band = (0.004, 0.004)
    correct = CoverageEnvelope((0, 0.004), (0, 1)).target_tail(band)
    assert correct == pytest.approx((0.003984, 0.007984))
    assert not score_decision(correct, 0.3, 234.5, 0.004, 0.6, 0.3).certified
    bad = CoverageEnvelope((0, 0.0005), (0, 1)).target_tail(band)
    assert bad[1] < 0.007984
    assert score_decision(bad, 0.3, 234.5, 0.004, 0.6, 0.3).certified


def test_endpoint_hull_contains_every_grid_value():
    band = CoverageEnvelope((0.1, 0.2), (0.05, 0.7)).target_tail((0.15, 0.6))
    for m in np.linspace(0.1, 0.2, 11):
        for p in np.linspace(0.15, 0.6, 11):
            for z in np.linspace(0.05, 0.7, 11):
                assert band[0] - 1e-12 <= (1 - m) * p + m * z <= band[1] + 1e-12


@pytest.mark.parametrize("p", [0.0, 0.001, 0.01, 0.2, 0.5, 0.98, 1.0])
def test_fixed_look_coverage_by_binomial_enumeration(p):
    n = 30
    miss = sum(
        comb(n, k) * p**k * (1 - p) ** (n - k)
        for k in range(n + 1)
        if not bernoulli_band(k, n, 0.05)[0] <= p <= bernoulli_band(k, n, 0.05)[1]
    )
    assert miss <= 0.05


def test_stratum_allocation_is_global_and_counts_cost():
    weights = (0.9, 0.1)
    plan = plan_units(64, (1, 2), weights)
    assert plan[0] + 2 * plan[1] == 64
    objective = weights[0] / sqrt(plan[0]) + weights[1] / sqrt(plan[1])
    assert objective == min(
        weights[0] / sqrt(a) + weights[1] / sqrt(b)
        for a in range(1, 64)
        for b in range(1, 32)
        if a + 2 * b <= 64
    )


def test_decisions_and_validation():
    assert score_decision((0.6, 0.6), 0, 1, 0.6, 0.6, 0).call == -1
    assert score_decision((0.5, 0.7), 0, 1, 0.6, 0.6, 0.2).call == 0
    with pytest.raises(ValueError, match="probability interval"):
        CoverageEnvelope((0, 1.1), (0, 1))
    with pytest.raises(ValueError, match="independent-unit"):
        bernoulli_band(11, 10, 0.05)
    with pytest.raises(ValueError, match="positive"):
        reachable_band((0, 0), (10, 10), (1, 0), 0.05)
    with pytest.raises(ValueError, match="budget"):
        plan_units(2, (1, 2), (0.9, 0.1))
