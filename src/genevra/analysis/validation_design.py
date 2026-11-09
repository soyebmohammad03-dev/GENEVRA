"""Finite-population reference bounds and fixed-look pilot planning."""

from dataclasses import dataclass
from enum import Enum
from math import ceil, comb, exp, fsum, lgamma, log, log1p, sqrt

from genevra.analysis.coverage_envelope import CoverageEnvelope, Interval, probability_interval


def _check_alpha(alpha: float) -> None:
    if not 0 < alpha < 1:
        raise ValueError("alpha must be between zero and one")


def binomial_lower_tail(k: int, n: int, p: float) -> float:
    """P(X <= k), evaluated in log space."""
    if not 0 <= k <= n or n < 1 or not 0 <= p <= 1:
        raise ValueError("invalid binomial inputs")
    if p == 0 or k == n:
        return 1.0
    if p == 1:
        return 0.0
    a, b, norm = log(p), log1p(-p), lgamma(n + 1)
    return min(
        1.0,
        fsum(
            exp(norm - lgamma(j + 1) - lgamma(n - j + 1) + j * a + (n - j) * b)
            for j in range(k + 1)
        ),
    )


def risk_upper(k: int, n: int, alpha: float) -> float:
    """One-sided Clopper–Pearson upper bound for independent Bernoulli episodes."""
    _check_alpha(alpha)
    if not 0 <= k <= n or n < 1:
        raise ValueError("invalid event counts")
    if k == n:
        return 1.0
    low, high = 0.0, 1.0
    for _ in range(53):
        mid = (low + high) / 2
        if binomial_lower_tail(k, n, mid) > alpha:
            low = mid
        else:
            high = mid
    return high


def passing_count(n: int, cap: float, alpha: float) -> int:
    """Largest count passing an exact safety gate, or -1 when none can pass."""
    _check_alpha(alpha)
    if n < 1 or not 0 < cap < 1:
        raise ValueError("invalid safety gate")
    low, high = -1, n
    while high - low > 1:
        k = (low + high) // 2
        if binomial_lower_tail(k, n, cap) <= alpha:
            low = k
        else:
            high = k
    return low


def paired_radius(n: int, alpha: float) -> float:
    """One-sided Hoeffding radius for independent differences in [-1, 1]."""
    _check_alpha(alpha)
    if n < 1:
        raise ValueError("no independent episodes")
    return sqrt(2 * log(1 / alpha) / n)


def planning_count(independent_count: int, cluster_size: int, icc: float, loss: float) -> int:
    """Variance-based planning sensitivity, not a substitute for clustered inference."""
    if independent_count < 1 or cluster_size < 1 or not 0 <= icc <= 1 or not 0 <= loss < 1:
        raise ValueError("invalid planning assumptions")
    return ceil(independent_count * (1 + (cluster_size - 1) * icc) / (1 - loss))


@dataclass(frozen=True)
class ReferenceStratum:
    """Roster size and fixed SRSWOR sample counts, including unresolved labels."""

    population: int
    sampled: int
    positive: int
    unresolved: int = 0

    def __post_init__(self) -> None:
        if (
            self.population < 1
            or not 0 <= self.sampled <= self.population
            or min(self.positive, self.unresolved) < 0
            or self.positive + self.unresolved > self.sampled
        ):
            raise ValueError("invalid reference stratum")

    def interval(self, alpha: float) -> Interval:
        _check_alpha(alpha)
        population, n = self.population, self.sampled
        if not n:
            return 0.0, 1.0
        denominator = comb(population, n)

        def tail(total: int, k: int, upper: bool) -> float:
            lo, hi = max(0, n - (population - total)), min(n, total)
            if upper:
                lo = max(lo, k)
            else:
                hi = min(hi, k)
            return (
                sum(comb(total, j) * comb(population - total, n - j) for j in range(lo, hi + 1))
                / denominator
            )

        # Upper tails grow with the population total, lower tails shrink.
        def endpoint(k: int, upper_tail: bool) -> int:
            lo, hi = -1, population + 1
            while hi - lo > 1:
                total = (hi + lo) // 2
                accepted = tail(total, k, upper_tail) >= alpha / 2
                if accepted == upper_tail:
                    hi = total
                else:
                    lo = total
            return hi if upper_tail else lo

        return endpoint(self.positive, True) / population, endpoint(
            self.positive + self.unresolved, False
        ) / population


def reference_band(
    strata: tuple[ReferenceStratum, ...], family_alpha: float, episodes: int, off_frame_cap: float
) -> Interval:
    """Allocate error across episodes and strata, then propagate a supplied mass cap."""
    _check_alpha(family_alpha)
    if not strata or episodes < 1:
        raise ValueError("empty reference design")
    size = sum(s.population for s in strata)
    bands = [
        (s.population / size, s.interval(family_alpha / (episodes * len(strata)))) for s in strata
    ]
    lo, hi = (fsum(weight * band[i] for weight, band in bands) for i in (0, 1))
    return CoverageEnvelope((0, off_frame_cap), (0, 1)).target_tail((max(0.0, lo), min(1.0, hi)))


class Verdict(Enum):
    ABSTAIN = "abstain"
    CORRECT = "adjudicated_correct"
    FALSE = "adjudicated_false"
    UNRESOLVED = "unresolved"


def adjudicate(reference: Interval, anchor: float, tolerance: float, issued: bool) -> Verdict:
    """Compare against the entire reference set, without imputing a true mean."""
    probability_interval(reference)
    if not 0 <= anchor <= 1 or not 0 <= tolerance <= 1:
        raise ValueError("invalid anchor or tolerance")
    if not issued:
        return Verdict.ABSTAIN
    lo, hi = anchor - tolerance, anchor + tolerance
    if lo <= reference[0] and reference[1] <= hi:
        return Verdict.CORRECT
    if reference[1] < lo or reference[0] > hi:
        return Verdict.FALSE
    return Verdict.UNRESOLVED


def paired_scores(
    candidate: Verdict, direct: Verdict, candidate_precise: bool, direct_precise: bool
) -> tuple[int, int]:
    """Conservative candidate adverse event and lower bound on useful gain."""
    adverse = candidate in (Verdict.FALSE, Verdict.UNRESOLVED)
    gain = int(candidate_precise and candidate is Verdict.CORRECT) - int(
        direct_precise and direct in (Verdict.CORRECT, Verdict.UNRESOLVED)
    )
    return int(adverse), gain


def comparable_package(
    candidate_id: str, direct_id: str, candidate_cost: int, direct_cost: int
) -> bool:
    """Require the same frozen package and integer charged cost units."""
    if min(candidate_cost, direct_cost) < 0:
        raise ValueError("negative acquisition cost")
    return bool(candidate_id) and candidate_id == direct_id and candidate_cost == direct_cost
