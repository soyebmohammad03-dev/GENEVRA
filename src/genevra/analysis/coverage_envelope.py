"""Fixed-look bounds for a two-stratum reachable population with incomplete coverage."""

from dataclasses import dataclass
from functools import lru_cache
from math import isclose, isfinite, log, log1p, sqrt

Interval = tuple[float, float]


def probability_interval(interval: Interval) -> None:
    if not 0 <= interval[0] <= interval[1] <= 1:
        raise ValueError("expected a closed probability interval")


@dataclass(frozen=True)
class CoverageEnvelope:
    """Externally justified bounds, conditional on independently defensible evidence."""

    missing_mass: Interval
    missing_tail: Interval

    def __post_init__(self) -> None:
        probability_interval(self.missing_mass)
        probability_interval(self.missing_tail)

    def target_tail(self, reachable_tail: Interval) -> Interval:
        """Exact range of the mixture over the rectangular identification region."""
        probability_interval(reachable_tail)
        values = [
            (1 - mass) * reachable + mass * missing
            for mass in self.missing_mass
            for reachable in reachable_tail
            for missing in self.missing_tail
        ]
        return min(values), max(values)


def _binary_kl(observed: float, candidate: float) -> float:
    if candidate in (0, 1):
        return 0.0 if observed == candidate else float("inf")
    left = observed * log(observed / candidate) if observed else 0.0
    right = (1 - observed) * (log1p(-observed) - log1p(-candidate)) if observed < 1 else 0.0
    return left + right


@lru_cache(maxsize=8192)
def bernoulli_band(successes: int, units: int, alpha: float) -> Interval:
    """Invert two binomial Chernoff tail bounds on independent observations."""
    if type(successes) is not int or type(units) is not int or not 0 <= successes <= units:
        raise ValueError("invalid independent-unit counts")
    if units == 0 or not 0 < alpha < 1:
        raise ValueError("no independent units or invalid error level")
    point = successes / units
    limit = log(2 / alpha) / units

    def invert(lo: float, hi: float, increasing: bool) -> float:
        for _ in range(48):
            mid = (lo + hi) / 2
            if (_binary_kl(point, mid) > limit) == increasing:
                hi = mid
            else:
                lo = mid
        return hi if increasing else lo

    return (
        invert(0, point, False) if successes else 0.0,
        invert(point, 1, True) if successes < units else 1.0,
    )


def _validate_weights(weights: tuple[float, float]) -> None:
    if any(not 0 < w < 1 for w in weights) or not isclose(sum(weights), 1, abs_tol=1e-12):
        raise ValueError("stratum weights must be positive and sum to one")


def reachable_band(
    counts: tuple[int, int], units: tuple[int, int], weights: tuple[float, float], alpha: float
) -> Interval:
    """Use simultaneous stratum bands, then mix by known reachable weights."""
    _validate_weights(weights)
    bands = tuple(bernoulli_band(k, n, alpha / 2) for k, n in zip(counts, units, strict=True))
    lo, hi = (sum(w * b[i] for w, b in zip(weights, bands, strict=True)) for i in (0, 1))
    return lo, hi


def plan_units(
    budget: int, tariffs: tuple[int, int], weights: tuple[float, float]
) -> tuple[int, int]:
    """Find the exact two-stratum optimum for sum(w_h/sqrt(n_h)) under a fixed budget."""
    _validate_weights(weights)
    if (
        type(budget) is not int
        or any(type(c) is not int or c <= 0 for c in tariffs)
        or budget < sum(tariffs)
    ):
        raise ValueError("budget must buy a unit in each stratum")
    low_cost, high_cost = tariffs
    best = (1, 1)
    objective = float("inf")
    for high in range(1, (budget - low_cost) // high_cost + 1):
        low = (budget - high_cost * high) // low_cost
        candidate = weights[0] / sqrt(low) + weights[1] / sqrt(high)
        if candidate < objective:
            objective, best = candidate, (low, high)
    return best


@dataclass(frozen=True)
class ScoreDecision:
    bounds: Interval
    call: int
    certified: bool


def score_decision(
    tail: Interval, body: float, rare: float, anchor: float, epsilon: float, tolerance: float
) -> ScoreDecision:
    """Keep threshold resolution separate from a uniform anchor certificate."""
    probability_interval(tail)
    if (
        not -240 <= body <= rare <= 240
        or not 0 <= anchor <= 1
        or not isfinite(epsilon)
        or not isfinite(tolerance)
        or tolerance < 0
    ):
        raise ValueError("invalid score support, anchor or threshold")
    span = rare - body
    lo, hi = (body + span * p for p in tail)
    call = 1 if lo > epsilon else -1 if hi <= epsilon else 0
    certified = span * max(abs(tail[0] - anchor), abs(tail[1] - anchor)) <= tolerance
    return ScoreDecision((lo, hi), call, certified)
