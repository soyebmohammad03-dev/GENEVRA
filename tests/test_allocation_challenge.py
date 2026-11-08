"""Cost, information, and pairing checks for Phase 25."""

import math
import runpy
from fractions import Fraction
from pathlib import Path

import pytest

API = runpy.run_path(
    str(Path(__file__).resolve().parents[1] / "experiments/allocation_challenge.py")
)
REQUEST = API["Request"]


@pytest.mark.parametrize("counts", [(0, 0), (128, 128), (0, 3), (4, 0), (56, 109)])
@pytest.mark.parametrize("costs", [(1, 2), (8, 16), (3, 7)])
def test_exact_integer_objective(counts, costs):
    budget = 29 * sum(costs)
    request = REQUEST(budget, costs, (0.9, 0.1), 2, counts, 128)
    chosen = API["variance_policy"](request)
    API["validate_allocation"](request, chosen)
    probabilities = [Fraction(2 * k + 1, 258) for k in counts]
    coefficients = [
        w * w * p * (1 - p)
        for w, p in zip((Fraction(9, 10), Fraction(1, 10)), probabilities, strict=True)
    ]

    def objective(a, b):
        return coefficients[0] / a + coefficients[1] / b

    feasible = [
        objective(a, b)
        for a in range(2, budget // costs[0] + 1)
        for b in range(2, budget // costs[1] + 1)
        if costs[0] * a + costs[1] * b == budget
    ]
    assert objective(*chosen) == min(feasible)


@pytest.mark.parametrize("hits", [(), (0, -1), (0, 129), (0, 2.0), (False, 1)])
def test_missing_or_invalid_pilot(hits):
    with pytest.raises(ValueError, match="pilot information"):
        API["variance_policy"](REQUEST(100, (1, 2), (0.9, 0.1), 1, hits, 128))


def test_infeasible_exact_budget_and_bad_entrant():
    r = REQUEST(17, (3, 6), (0.9, 0.1), 1, (0, 0), 128)
    with pytest.raises(ValueError, match="no exact-spend"):
        API["variance_policy"](r)
    for bad in [(1, 1), (17, 0), (5.0, 2), (True, 1)]:
        with pytest.raises(ValueError):
            API["validate_allocation"](r, bad)


def test_common_prefix_invariant_to_entrant():
    design, cfg = API["load_design"]()
    case, budget = cfg["cases"][0], cfg["budgets"][0]
    args = (design["seed"], 0, 0, 11, case, budget, cfg, design)
    ordinary = API["observations"](*args, None)

    def entrant(request):
        assert set(request._fields) == {
            "budget",
            "costs",
            "weights",
            "minimum",
            "pilot_hits",
            "pilot_n",
        }
        return request.budget - 2, 1

    augmented = API["observations"](*args, entrant)
    assert ordinary[:2] == augmented[:2]
    for method in ordinary[2]:
        assert ordinary[2][method] == augmented[2][method]
        assert ordinary[3][method] == augmented[3][method]
    for h in range(2):
        pairs = sorted((ordinary[2][m][h], ordinary[3][m][h]) for m in ordinary[2])
        assert all(
            0 <= y - x <= b - a for (a, x), (b, y) in zip(pairs[:-1], pairs[1:], strict=True)
        )


def test_duplicated_rows_charged_but_not_independent():
    design, cfg = API["load_design"]()
    case = cfg["cases"][-1]
    request, pilot_cost, allocations, _ = API["observations"](
        design["seed"], 8, 0, 0, case, 8192, cfg, design, None
    )
    assert request.costs == (8, 16)
    assert pilot_cost == 3072
    assert request.budget == 5120
    for n0, n1 in allocations.values():
        assert 8 * n0 + 16 * n1 + pilot_cost == 8192


def test_zero_hits_band_and_paired_interval():
    _, cfg = API["load_design"]()
    out = API["score"]((0, 0), (100, 100), cfg["cases"][0], cfg, 0.3, "direct")
    assert out["high"] == pytest.approx(0.3 + 234.2 * (1 - (0.05 / 4) ** (1 / 100)))
    assert out["coverage"] == 1
    mean, low, high = API["paired"]([0] * 256, 0.05)
    assert mean == 0
    assert high == pytest.approx(math.sqrt(math.log(40) / 128))
    assert low == -high
