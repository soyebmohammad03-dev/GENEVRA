"""Check safety arithmetic, design coverage and conservative episode scoring."""

from math import comb

import pytest

from genevra.analysis.validation_design import (
    ReferenceStratum,
    Verdict,
    adjudicate,
    binomial_lower_tail,
    comparable_package,
    paired_radius,
    paired_scores,
    passing_count,
    planning_count,
    reference_band,
    risk_upper,
)


def test_pilot_cannot_clear_the_safety_gate():
    assert risk_upper(0, 12, 0.02) == pytest.approx(1 - 0.02 ** (1 / 12))
    assert passing_count(12, 0.05, 0.02) == -1
    assert passing_count(76, 0.05, 0.02) == -1
    assert passing_count(77, 0.05, 0.02) == 0
    assert passing_count(209, 0.05, 0.02) == 4
    assert binomial_lower_tail(4, 209, 0.01) == pytest.approx(0.9398060281)
    assert 0.2 - paired_radius(782, 0.02) < 0.1 < 0.2 - paired_radius(783, 0.02)
    assert planning_count(100, 4, 0.2, 0.2) == 200


@pytest.mark.parametrize("total", range(11))
def test_exact_reference_interval_has_design_coverage(total):
    population, sample, alpha = 10, 5, 0.2
    coverage = 0.0
    for positive in range(max(0, sample - population + total), min(sample, total) + 1):
        lo, hi = ReferenceStratum(population, sample, positive).interval(alpha)
        if lo <= total / population <= hi:
            coverage += comb(total, positive) * comb(population - total, sample - positive)
    assert coverage / comb(population, sample) >= 1 - alpha - 1e-12


def test_complete_reference_detects_shared_blindness():
    reachable = ReferenceStratum(90, 90, 9)
    hidden = ReferenceStratum(10, 10, 10)
    band = reference_band((reachable, hidden), 0.01, 1, 0)
    assert band == pytest.approx((0.19, 0.19))
    assert adjudicate(band, 0.10, 0.05, True) is Verdict.FALSE
    assert adjudicate(band, 0.10, 0.05, False) is Verdict.ABSTAIN
    assert adjudicate((0.1, 0.1), 0.1, 0.05, True) is Verdict.CORRECT


def test_unresolved_and_reference_frame_error_propagate():
    assert ReferenceStratum(10, 10, 3, 2).interval(0.05) == (0.3, 0.5)
    assert ReferenceStratum(10, 0, 0).interval(0.05) == (0.0, 1.0)
    incomplete = reference_band((ReferenceStratum(90, 90, 9),), 0.01, 1, 0.1)
    assert incomplete == pytest.approx((0.09, 0.19))
    assert adjudicate(incomplete, 0.1, 0.05, True) is Verdict.UNRESOLVED
    assert paired_scores(Verdict.UNRESOLVED, Verdict.UNRESOLVED, True, True) == (1, -1)
    assert paired_scores(Verdict.FALSE, Verdict.CORRECT, True, True) == (1, -1)


def test_cost_and_package_must_match():
    assert comparable_package("ledger-a", "ledger-a", 40, 40)
    assert not comparable_package("ledger-a", "ledger-b", 40, 40)
    assert not comparable_package("ledger-a", "ledger-a", 40, 41)
    with pytest.raises(ValueError):
        comparable_package("ledger-a", "ledger-a", -1, -1)


def test_validation_rejects_invalid_input():
    with pytest.raises(ValueError):
        ReferenceStratum(10, 3, 2, 2)
    with pytest.raises(ValueError):
        adjudicate((0.6, 0.5), 0.5, 0.1, True)
