"""Separate GENEVRA reference calculations from frozen counts and decisions."""

import argparse
import csv
import hashlib
import json
import math
from collections import defaultdict
from functools import lru_cache
from pathlib import Path
from statistics import mean, median

ROOT = Path(__file__).resolve().parents[1]
ALLOCATION = ROOT / "docs/research/phase_25"
CONFIG = ROOT / "docs/model_repair/phase_19/extension/config.json"
METHODS = {
    "width_proxy",
    "variance",
    "minimax",
    "equal_spend",
    "proportional",
    "direct",
    "oracle",
    "abstain",
}
SCORE_BASE, SPAN = 0.3, 234.2
TOLERANCE = 1e-9


def require(condition, label):
    if not condition:
        raise ValueError(f"reference verification failed: {label}")


def sha(path):
    with path.open("rb") as f:
        return hashlib.file_digest(f, "sha256").hexdigest()


def same(a, b):
    return abs(a - b) <= TOLERANCE


def score(probability):
    return SCORE_BASE + SPAN * probability


@lru_cache(maxsize=16384)
def bernoulli_limits(k, n, alpha):
    """Invert the two-stratum fixed-look likelihood threshold in rate space."""
    require(type(k) is int and type(n) is int and 0 <= k <= n and n > 0, "binomial count")
    require(0 < alpha < 1, "alpha")
    target = math.log(alpha / 4) / n
    if k == 0:
        return 0.0, -math.expm1(target)
    if k == n:
        return math.exp(target), 1.0
    p = k / n

    def log_ratio(q):
        return p * math.log(q / p) + (1 - p) * math.log((1 - q) / (1 - p))

    def crossing(left, right, rising):
        for _ in range(55):
            q = (left + right) * 0.5
            if q in (left, right):
                break
            if (log_ratio(q) < target) == rising:
                left = q
            else:
                right = q
        return (left + right) * 0.5

    return crossing(0.0, p, True), crossing(p, 1.0, False)


def envelope(lo, hi, cap, hidden_cap):
    """Closed-form hull for m in [0, cap] and z in [0, hidden_cap]."""
    require(0 <= lo <= hi <= 1 and 0 <= cap <= 1 and 0 <= hidden_cap <= 1, "hull domain")
    return (1 - cap) * lo, hi + cap * max(hidden_cap - hi, 0.0)


def allocation_interval(counts, units, weights, alpha, cap=0.0, hidden_cap=1.0):
    limits = [bernoulli_limits(k, n, alpha) for k, n in zip(counts, units, strict=True)]
    lo, hi = (
        math.fsum(w * x for w, x in zip(weights, axis, strict=True))
        for axis in zip(*limits, strict=True)
    )
    return tuple(score(x) for x in envelope(lo, hi, cap, hidden_cap))


def classify(low, high, truth, epsilon, width_limit, certificate, anchor_error, tolerance):
    require(all(math.isfinite(v) for v in (low, high, truth)) and low <= high, "interval")
    require(type(certificate) is bool, "certificate flag")
    covered = low <= truth <= high
    call = -1 if high <= epsilon else 1 if low > epsilon else 0
    false = certificate and anchor_error > tolerance
    width = high - low
    return {
        "call": call,
        "width": width,
        "coverage": int(covered),
        "useful": int(covered and width <= width_limit),
        "abstention": int(call == 0),
        "wrong_call": int(call != 0 and call != (1 if truth > epsilon else -1)),
        "certificate": int(certificate),
        "false_certificate": int(false),
        "utility": int(certificate) - 2 * int(false),
    }


@lru_cache(maxsize=2048)
def optimal_high(budget, tariffs, weights, variances):
    """Find the first discrete convex minimum using adjacent differences."""
    c0, c1 = tariffs
    require(c1 % c0 == 0 and budget % c0 == 0 and budget >= c0 + c1, "tariff grid")
    end = (budget - c0) // c1

    def objective(high):
        low = (budget - c1 * high) // c0
        if variances is None:
            return weights[0] / math.sqrt(low) + weights[1] / math.sqrt(high)
        return weights[0] ** 2 * variances[0] / low + weights[1] ** 2 * variances[1] / high

    left, right = 1, end
    while left < right:
        mid = (left + right) // 2
        if objective(mid + 1) < objective(mid):
            left = mid + 1
        else:
            right = mid
    return left


def check_budget(method, units, hits, tariff, budget, pilot, size, rates, weights):
    a, b = units
    require(min(a, b) > 0 and all(0 <= k <= n for k, n in zip(hits, units, strict=True)), method)
    require(all(0 <= k <= size for k in pilot), "pilot count")
    remaining = budget - size * sum(tariff)
    require(a * tariff[0] + b * tariff[1] == remaining, "matched acquisition cost")
    if method in {"equal_spend", "direct"}:
        expected = remaining // (2 * tariff[1])
    elif method == "proportional":
        expected = round(
            remaining * weights[1] / sum(c * w for c, w in zip(tariff, weights, strict=True))
        )
    else:
        q = tuple((k + 0.5) / (size + 1) for k in pilot) if method == "variance" else rates
        variance = tuple(p * (1 - p) for p in q)
        if method == "width_proxy":
            variance = None
        if method == "minimax":
            variance = (0.25, 0.25)
        expected = optimal_high(remaining, tariff, weights, variance)
    require(b == expected, (method, "integer allocation"))


def hoeffding(differences, alpha, limit):
    require(bool(differences) and all(-limit <= d <= limit for d in differences), "contrast range")
    n = len(differences)
    estimate = math.fsum(differences) / n
    radius = limit * math.sqrt(2 * math.log(2 / alpha) / n)
    return [estimate, max(-limit, estimate - radius), min(limit, estimate + radius)]


def binomial_upper(k, n, alpha):
    """One-sided exact upper bound by inverting the lower binomial tail."""
    require(0 <= k <= n and n > 0 and 0 < alpha < 1, "exact binomial inputs")
    if k == n:
        return 1.0
    coefficients = [math.comb(n, j) for j in range(k + 1)]
    left, right = 0.0, 1.0
    for _ in range(52):
        p = (left + right) / 2
        cdf = math.fsum(c * p**j * (1 - p) ** (n - j) for j, c in enumerate(coefficients))
        if cdf > alpha:
            left = p
        else:
            right = p
    return (left + right) / 2


def summarize_allocation(raw):
    receipt = json.loads((ALLOCATION / "receipt.json").read_text())
    require(sha(raw) == receipt["outputs"]["raw.csv"], "published Phase 25 raw hash")
    require(sha(CONFIG) == receipt["design"]["phase19_config_sha256"], "Phase 19 config")
    cfg = json.loads(CONFIG.read_text())
    cases = {row["name"]: row for row in cfg["cases"]}
    weights = tuple(cfg["weights"])
    size = receipt["design"]["pilot_per_stratum"]
    n = receipt["design"]["replicates"]
    groups = defaultdict(dict)
    with raw.open(newline="", encoding="utf-8") as stream:
        for row in csv.DictReader(stream):
            case, total = row["case"], int(row["budget"])
            replicate, method = int(row["replicate"]), row["method"]
            key = case, total, method
            require(
                method in METHODS
                and total in cfg["budgets"]
                and 0 <= replicate < n
                and replicate not in groups[key],
                ("row identity", key, replicate),
            )
            c = cases[case]
            reachable = sum(w * p for w, p in zip(weights, c["rates"], strict=True))
            target = (1 - c["mass"]) * reachable + c["mass"] * c["hidden"]
            units = int(row["n0"]), int(row["n1"])
            hits = int(row["k0"]), int(row["k1"])
            tariffs = tuple(x * c["block"] for x in cfg["tariffs"])
            if method == "abstain":
                require(
                    units == hits == (0, 0)
                    and not row["pilot0"]
                    and not row["pilot1"]
                    and row["cost"] == row["pilot_cost"] == "0",
                    "abstention input",
                )
                low, high, certificate = -240.0, 240.0, False
            else:
                pilot = int(row["pilot0"]), int(row["pilot1"])
                check_budget(method, units, hits, tariffs, total, pilot, size, c["rates"], weights)
                require(
                    int(row["cost"]) == total and int(row["pilot_cost"]) == size * sum(tariffs),
                    "tariff metadata",
                )
                low, high = allocation_interval(
                    hits,
                    units,
                    weights,
                    cfg["alpha"],
                    0.0 if method == "direct" else c["cap"],
                    c["hidden_cap"],
                )
                certificate = (
                    max(abs(low - score(cfg["anchor"])), abs(high - score(cfg["anchor"])))
                    <= cfg["tolerance"]
                )
            values = classify(
                low,
                high,
                score(target),
                cfg["epsilon"],
                cfg["target_width"],
                certificate,
                SPAN * abs(target - cfg["anchor"]),
                cfg["tolerance"],
            )
            require(
                same(low, float(row["low"])) and same(high, float(row["high"])), ("bounds", key)
            )
            require(same(score(target), float(row["truth"])), ("target", key))
            for metric, value in values.items():
                require(same(float(row[metric]), value), (key, metric, replicate))
            groups[key][replicate] = values
    expected = {(c, b, m) for c in cases for b in cfg["budgets"] for m in METHODS}
    require(set(groups) == expected and all(len(v) == n for v in groups.values()), "cell inventory")
    return groups, n


def compare_allocation(groups, n):
    published = json.loads((ALLOCATION / "results.json").read_text())
    require(len(published["summary"]) == len(groups), "published inventory")
    cells = []
    for row in published["summary"]:
        key = row["case"], row["budget"], row["method"]
        records = list(groups[key].values())
        metrics = {
            k: sum(r[k] for r in records)
            for k in (
                "coverage",
                "useful",
                "abstention",
                "wrong_call",
                "certificate",
                "false_certificate",
            )
        }
        for k, v in metrics.items():
            require(row[k]["count"] == v, (key, k))
        require(same(row["median_width"], median(r["width"] for r in records)), ("median", key))
        require(same(row["utility"], mean(r["utility"] for r in records)), ("utility", key))
        cells.append({"case": key[0], "budget": key[1], "method": key[2], **metrics})
    contrasts = []
    require(len(published["contrasts"]) == 18, "contrast inventory")
    for row in published["contrasts"]:
        c, b = row["case"], row["budget"]
        primary = (c, b) == ("small_omission", 32768)
        require(row["primary"] == primary, "contrast family")
        proxy, variance = (groups[c, b, m] for m in ("width_proxy", "variance"))
        differences = [proxy[i]["useful"] - variance[i]["useful"] for i in range(n)]
        alpha = 0.05 if primary else 0.05 / 17
        estimate, low, high = hoeffding(differences, alpha, 1.0)
        require(
            all(
                same(v, row[k]) for k, v in (("difference", estimate), ("low", low), ("high", high))
            ),
            (c, b, "paired interval"),
        )
        contrasts.append(
            {
                "case": c,
                "budget": b,
                "primary": primary,
                "n": n,
                "alpha": alpha,
                "difference": estimate,
                "interval": [low, high],
                "proxy_only": differences.count(1),
                "variance_only": differences.count(-1),
            }
        )
    return {"replicate_records": len(groups) * n, "cells": cells, "contrasts": contrasts}


def phase18_checks(replay):
    # NumPy is solely a file-format adapter for the frozen NPZ decisions.
    import numpy as np

    archive = replay / "archive/phase-18"
    cfg = json.loads((archive / "docs/model_repair/phase_18/config.json").read_text())
    records = replay / "phase-18"
    n = cfg["replicates"]
    utility, counts = {}, {}
    with np.load(records / "replicates.npz", allow_pickle=False) as decisions:
        for i, case in enumerate(cfg["cases"]):
            name = case["name"]
            raw = json.loads((archive / f"raw/cells/{i}.json").read_text())["payload"]
            require(raw["key"] == [i] and len(raw["source_tail"]) == n, "Phase 18 cell")
            p = (1 - case["weight"]) * 0.0002 + case["weight"] * case["target_high"]
            errors = [SPAN * abs(k / cfg["source_rows"] - p) for k in raw["source_tail"]]
            methods = ["combined", "direct", "stratified", "abstain"]
            if case["regime"] == "registered":
                methods.append("pooled")
            for method in methods:
                prefix = f"{name}_{method}"
                bands = decisions[f"{prefix}_interval"]
                certificates = decisions[f"{prefix}_cert"]
                require(bands.shape == (n, 2) and certificates.shape == (n,), prefix)
                outcomes = [
                    classify(
                        float(lo),
                        float(hi),
                        score(p),
                        cfg["epsilon"],
                        cfg["width_target"],
                        bool(cert),
                        err,
                        cfg["transfer_tolerance"],
                    )
                    for (lo, hi), cert, err in zip(bands, certificates, errors, strict=True)
                ]
                utility[name, method] = [r["utility"] for r in outcomes]
                counts[name, method] = {
                    key: sum(r[key] for r in outcomes)
                    for key in (
                        "coverage",
                        "abstention",
                        "wrong_call",
                        "certificate",
                        "false_certificate",
                    )
                }
    with (records / "rates.csv").open(newline="", encoding="utf-8") as f:
        historical = {
            (r["case"], r["method"], r["metric"]): int(r["count"]) for r in csv.DictReader(f)
        }
    names = {
        "coverage": "coverage",
        "abstention": "abstention",
        "wrong_call": "false_label",
        "certificate": "certification",
        "false_certificate": "false_certification",
    }
    for (c, m), values in counts.items():
        require(all(historical[c, m, names[k]] == v for k, v in values.items()), (c, m))
    contrasts = {}
    with (records / "primary.csv").open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            method = row["comparator"]
            d = [
                a - b
                for case in cfg["primary_cases"]
                for a, b in zip(utility[case, "combined"], utility[case, method], strict=True)
            ]
            result = hoeffding(d, 0.05 / 3, 2.0)
            require(
                all(
                    same(v, float(row[k]))
                    for v, k in zip(result, ("difference", "low", "high"), strict=True)
                ),
                method,
            )
            contrasts[method] = result
    require(set(contrasts) == {"direct", "stratified", "abstain"}, "Phase 18 contrasts")
    safety = {}
    with (records / "summary.csv").open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row["method"] != "combined":
                continue
            case = row["case"]
            k = counts[case, "combined"]["false_certificate"]
            upper = binomial_upper(k, n, 0.05 / len(cfg["cases"]))
            require(same(upper, float(row["simultaneous_false_upper"])), (case, "exact safety"))
            safety[case] = upper
    require(len(safety) == len(cfg["cases"]), "safety family")
    return {
        "simultaneous_false_certificate_upper": safety,
        "shared_blind": counts["shared_blind", "combined"],
        "contrast_order": [
            "difference",
            "low",
            "high",
        ],
        "contrasts": contrasts,
        "method_cells": len(counts),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--phase25-raw", type=Path, required=True)
    parser.add_argument("--replay", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    groups, n = summarize_allocation(args.phase25_raw)
    report = {
        "schema": "genevra-reference-v1",
        "status": "passed",
        "absolute_numeric_tolerance": TOLERANCE,
        "phase25_raw_sha256": sha(args.phase25_raw),
        "reference_sha256": sha(Path(__file__)),
        "phase18": phase18_checks(args.replay),
        "phase25": compare_allocation(groups, n),
    }
    with args.output.open("x", encoding="utf-8") as stream:
        json.dump(report, stream, indent=2, allow_nan=False)
        stream.write("\n")


if __name__ == "__main__":
    main()
