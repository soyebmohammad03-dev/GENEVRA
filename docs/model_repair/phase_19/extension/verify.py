"""Audit the frozen coverage-envelope results without importing GENEVRA."""

import hashlib
import json
import math
import sys
from pathlib import Path
from statistics import NormalDist

import numpy as np


def band(k, n, alpha):
    """Vectorized likelihood-ratio inversion on a long-double grid."""
    k = np.asarray(k, dtype=np.longdouble)
    phat = k / n
    with np.errstate(divide="ignore", invalid="ignore"):
        peak = np.where(k > 0, k * np.log(phat), 0)
        peak += np.where(k < n, (n - k) * np.log1p(-phat), 0)
        limit = peak - math.log(4 / alpha)

        def root(lo, hi, lower):
            for _ in range(50):
                x = (lo + hi) / 2
                log_likelihood = np.where(k > 0, k * np.log(x), 0)
                log_likelihood += np.where(k < n, (n - k) * np.log1p(-x), 0)
                keep_upper = (log_likelihood < limit) != lower
                hi = np.where(keep_upper, x, hi)
                lo = np.where(keep_upper, lo, x)
            return (lo + hi) / 2

        return np.array(
            [root(np.zeros_like(phat), phat, True), root(phat, np.ones_like(phat), False)]
        )


def expand(interval, mass_cap, tail_cap):
    lo, hi = interval
    return np.array(
        [(1 - mass_cap) * lo, np.maximum(hi, (1 - mass_cap) * hi + mass_cap * tail_cap)]
    )


def check(expected, observed):
    np.testing.assert_allclose(expected, observed, atol=1e-9, rtol=0)


def main():
    config, raw, result = map(Path, sys.argv[1:])
    cfg = json.loads(config.read_text())
    raw_record = json.loads(raw.read_text())
    records = raw_record["records"]
    for name, sha in raw_record["identity"]["freeze"].items():
        assert hashlib.sha256(config.with_name(name).read_bytes()).hexdigest() == sha
    observed = json.loads(result.read_text())
    table = {(r["case"], r["budget"], r["method"]): r for r in observed["summary"]}
    n = cfg["replicates"]
    assert len(table) == len(observed["summary"])
    assert observed["replicates"] == len(cfg["cases"]) * len(cfg["budgets"]) * n
    costs = cfg["tariffs"]
    alpha = cfg["alpha"]
    eps, tol, anchor = (cfg[k] for k in ("epsilon", "tolerance", "anchor"))
    primary = None
    order = [(i, j) for i in range(len(cfg["cases"])) for j in range(len(cfg["budgets"]))]
    for (i, j), record in zip(order, records, strict=True):
        case, budget = cfg["cases"][i], cfg["budgets"][j]
        name, block = case["name"], case["block"]
        assert [name, budget, block] == [record[key] for key in ("case", "budget", "block")]
        assert record["seeds"] == [[cfg["seed"], i, j, h] for h in range(2)]
        sizes = record["units"]
        c0, c1 = (c * block for c in costs)
        candidate_high = np.arange(1, (budget - c0) // c1 + 1)
        candidate_low = (budget - c1 * candidate_high) // c0
        objective = cfg["weights"][0] / np.sqrt(candidate_low)
        objective += cfg["weights"][1] / np.sqrt(candidate_high)
        arg = int(objective.argmin())
        assert sizes["planned"] == [candidate_low[arg], candidate_high[arg]]
        assert sizes["equal"] == [budget // (2 * c0), budget // (2 * c1)]
        assert all(np.dot(units, [c0, c1]) == budget for units in sizes.values())
        k = record["counts_by_stratum"]
        for h in range(2):
            k_equal, k_plan = np.asarray(k["equal"][h]), np.asarray(k["planned"][h])
            assert k_equal.shape == k_plan.shape == (n,)
            n0, n1 = sizes["equal"][h], sizes["planned"][h]
            assert np.all((k_equal >= 0) & (k_equal <= n0))
            assert np.all((k_plan >= 0) & (k_plan <= n1))
            assert np.all((k_plan - k_equal) * (n1 - n0) >= 0)
            assert np.all(abs(k_plan - k_equal) <= abs(n1 - n0))
        bounds = {
            design: sum(
                w * band(k[design][h], units[h], alpha) for h, w in enumerate(cfg["weights"])
            )
            for design, units in sizes.items()
        }
        m, u, z, v = (case[key] for key in ("mass", "cap", "hidden", "hidden_cap"))
        reach = np.dot(cfg["weights"], case["rates"])
        p = reach + m * (z - reach)
        truth = 0.3 + 234.2 * p
        oracle = expand([reach, reach], u, v)
        targets = {
            "reachable_only": bounds["equal"],
            "equal_envelope": expand(bounds["equal"], u, v),
            "planned_envelope": expand(bounds["planned"], u, v),
            "full_hidden_support": expand(bounds["planned"], u, 1),
        }
        useful = {}
        for method in (*targets, "abstain"):
            result_row = table.pop((name, budget, method))
            if method == "abstain":
                low, high = np.full(n, -240.0), np.full(n, 240.0)
                cert = np.zeros(n, dtype=bool)
                units = [0, 0]
            else:
                target = targets[method]
                low, high = 0.3 + 234.2 * target
                cert = (target[0] >= anchor - tol / 234.2) & (target[1] <= anchor + tol / 234.2)
                units = sizes[
                    "planned" if method in ("planned_envelope", "full_hidden_support") else "equal"
                ]
            call = (low > eps).astype(int) - (high <= eps).astype(int)
            cover = (low <= truth) & (high >= truth)
            precision = high - low <= cfg["target_width"]
            useful[method] = cover & precision
            check(
                [
                    truth,
                    np.median(high - low),
                    np.quantile(high - low, 0.9),
                    234.2 * (oracle[1] - oracle[0]),
                ],
                [result_row[x] for x in ("truth", "median_width", "p90_width", "oracle_width")],
            )
            assert result_row["independent_units"] == units
            assert result_row["charged_rows"] == sum(units) * block
            assert result_row["acquisition_cost"] == np.dot(units, [c0, c1])
            for metric, indicator in {
                "coverage": cover,
                "precision": precision,
                "coverage_with_precision": cover & precision,
                "correct_decisive_coverage": cover & (call == (1 if truth > eps else -1)),
                "abstention": call == 0,
                "certificate": cert,
                "false_certificate": cert & (234.2 * abs(p - anchor) > tol),
            }.items():
                r = result_row["rates"][metric]
                events = int(indicator.sum())
                assert (r["count"], r["n"]) == (events, n), (name, budget, method, metric)
                normal = NormalDist().inv_cdf(0.975)
                center = (2 * events + normal**2) / (2 * (n + normal**2))
                radius = (
                    normal
                    * math.sqrt(4 * events * (1 - events / n) + normal**2)
                    / (2 * (n + normal**2))
                )
                check([max(0, center - radius), min(1, center + radius)], r["wilson"])
                check(events / n, r["rate"])
        if name == "small_omission" and budget == 32768:
            primary = float(useful["planned_envelope"].mean() - useful["equal_envelope"].mean())
    assert not table and primary is not None
    r = observed["primary"]
    radius = math.sqrt(2 * math.log(2 / 0.05) / n)
    check(
        [primary, max(-1, primary - radius), min(1, primary + radius)],
        [r["difference"], *r["interval"]],
    )
    assert r["n"] == n and r["passes"] == (primary - radius > 0.05)
    print(
        f"Verified {len(records)} cells, {observed['replicates']} paired replicates, "
        "90 method rows and 630 rates."
    )


if __name__ == "__main__":
    main()
