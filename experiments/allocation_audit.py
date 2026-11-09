"""Reconstruct GENEVRA Phase 25 and run the bounded Phase 26 sensitivity audit."""

import argparse
import csv
import json
import math
import statistics
from collections import defaultdict
from pathlib import Path

import allocation_challenge as prior
import numpy as np

from scripts.verify_allocation_challenge import band, close, independent_bounds, require, verify

ROOT = Path(__file__).resolve().parents[1]
PHASE = ROOT / "docs/research/phase_26"
FROZEN = {
    "design.json": "21cf64d567b35da57130805a64ee7feec4d0c83160c27d87c942e884ef973bec",
    "PROTOCOL.md": "57d17c22eaa1e3d20b09261915c3e693285acc48f58df367642e4f37b847ba3b",
}


def shares(weights, costs, variances=None):
    """Continuous allocation direction for width proxy or variance loss."""
    if variances is None:
        return [(w / c) ** (2 / 3) for w, c in zip(weights, costs, strict=True)]
    return [w * math.sqrt(v / c) for w, c, v in zip(weights, costs, variances, strict=True)]


def continuous_high(budget, costs, weights, variances=None):
    direction = shares(weights, costs, variances)
    return budget * direction[1] / math.fsum(c * d for c, d in zip(costs, direction, strict=True))


def convex_grid_check(chosen, budget, costs, weights, variances=None):
    """Check the integer optimum using convexity and the two enclosing grid points."""
    c0, c1 = costs
    require(c1 % c0 == budget % c0 == 0, "unsupported historical tariff grid")
    top = (budget - c0) // c1
    x = min(top, max(1, continuous_high(budget, costs, weights, variances)))

    def objective(h):
        lo = (budget - c1 * h) // c0
        if variances is None:
            return weights[0] / math.sqrt(lo) + weights[1] / math.sqrt(h)
        return weights[0] ** 2 * variances[0] / lo + weights[1] ** 2 * variances[1] / h

    best = min(objective(math.floor(x)), objective(math.ceil(x)))
    require(
        math.isclose(objective(chosen), best, abs_tol=1e-18, rel_tol=1e-12),
        "integer objective minimum",
    )
    return x


def reconstruction(directory):
    published = json.loads((ROOT / "docs/research/phase_25/receipt.json").read_text())
    require(
        json.loads((directory / "receipt.json").read_text()) == published,
        "published Phase 25 provenance and hashes",
    )
    verify(directory)
    design, cfg = prior.load_design()
    cases = {c["name"]: (i, c) for i, c in enumerate(cfg["cases"])}
    budgets = {b: j for j, b in enumerate(cfg["budgets"])}
    groups = defaultdict(dict)
    with (directory / "raw.csv").open(newline="") as f:
        for row in csv.DictReader(f):
            key = row["case"], int(row["budget"]), int(row["replicate"])
            groups[key][row["method"]] = row
    primary = defaultdict(list)
    effects = defaultdict(list)
    max_grid_shift = defaultdict(float)
    max_endpoint_error = 0.0
    for (name, total, replicate), methods in groups.items():
        i, case = cases[name]
        seed = (design["seed"], i, budgets[total], replicate)
        size = design["pilot_per_stratum"]
        pilot = np.random.default_rng((*seed, 0)).binomial(size, case["rates"])
        abstain = methods["abstain"]
        require((float(abstain["low"]), float(abstain["high"])) == (-240, 240), "abstention bounds")
        paid = {k: r for k, r in methods.items() if k != "abstain"}
        counts = {k: (int(r["n0"]), int(r["n1"])) for k, r in paid.items()}
        tariffs = tuple(c * case["block"] for c in cfg["tariffs"])
        available = total - size * sum(tariffs)
        w = cfg["weights"]
        props = [(int(k) + 0.5) / (size + 1) for k in pilot]
        true_var = [p * (1 - p) for p in case["rates"]]
        variance = [p * (1 - p) for p in props]
        streams = [
            np.random.default_rng((*seed, 1, h)).random(max(x[h] for x in counts.values())) < p
            for h, p in enumerate(case["rates"])
        ]
        for k, row in paid.items():
            n0, n1 = counts[k]
            hits = tuple(
                int(np.count_nonzero(s[:n])) for s, n in zip(streams, (n0, n1), strict=True)
            )
            require(hits == (int(row["k0"]), int(row["k1"])), "stratum-prefix count")
            require(tuple(pilot) == (int(row["pilot0"]), int(row["pilot1"])), "pilot RNG")
            if k in ("width_proxy", "variance", "oracle", "minimax"):
                coefficients = {
                    "width_proxy": None,
                    "variance": variance,
                    "oracle": true_var,
                    "minimax": [0.25, 0.25],
                }[k]
                center = convex_grid_check(n1, available, tariffs, w, coefficients)
                max_grid_shift[k] = max(max_grid_shift[k], abs(n1 - center))
            else:
                expected = (
                    round(
                        available * w[1] / math.fsum(c * z for c, z in zip(tariffs, w, strict=True))
                    )
                    if k == "proportional"
                    else available // (2 * tariffs[1])
                )
                require(n1 == expected, "fixed allocation")
            lo, hi = independent_bounds(hits, (n0, n1), w, case, cfg["alpha"], k)
            errors = abs(lo - float(row["low"])), abs(hi - float(row["high"]))
            require(close(lo, float(row["low"])) and close(hi, float(row["high"])), "endpoints")
            max_endpoint_error = max(max_endpoint_error, *errors)
            if (name, total) == ("small_omission", 32768):
                widths = [
                    w[h] * prior.SPAN * (b[1] - b[0])
                    for h, (hit, n) in enumerate(zip(hits, (n0, n1), strict=True))
                    for b in [band(hit, n, cfg["alpha"])]
                ]
                primary[k].append(
                    {
                        "n0": n0,
                        "n1": n1,
                        "useful": int(row["useful"]),
                        "width": hi - lo,
                        "low_stratum_width": widths[0],
                        "high_stratum_width": widths[1],
                        "envelope_increment": hi - lo - sum(widths),
                        "true_variance": sum(
                            w[h] ** 2 * true_var[h] / n for h, n in enumerate((n0, n1))
                        ),
                    }
                )
        effects[name, total].append(
            int(methods["width_proxy"]["useful"]) - int(methods["variance"]["useful"])
        )
    contrasts = []
    for (name, budget), differences in effects.items():
        is_primary = (name, budget) == ("small_omission", 32768)
        n = len(differences)
        point = statistics.mean(differences)
        alpha = design["comparative_alpha"] / (1 if is_primary else 17)
        half = math.sqrt(2 * math.log(2 / alpha) / n)
        contrasts.append(
            {
                "case": name,
                "budget": budget,
                "primary": is_primary,
                "n": n,
                "difference": point,
                "interval": [max(-1, point - half), min(1, point + half)],
                "proxy_only": differences.count(1),
                "variance_only": differences.count(-1),
            }
        )
    return {
        "phase25_raw_sha256": published["outputs"]["raw.csv"],
        "matched_replicates": len(groups),
        "all_method_intervals_checked": len(groups) * 8,
        "max_endpoint_discrepancy": max_endpoint_error,
        "max_integer_displacement_in_high_stratum": dict(max_grid_shift),
        "primary_diagnostics": {
            k: {f"mean_{key}": statistics.mean(r[key] for r in rows) for key in rows[0]}
            for k, rows in primary.items()
        },
        "contrasts": contrasts,
    }


def sensitivity_allocation(request, rates):
    c0, c1 = request.costs
    b, w = request.budget, request.weights
    high = round(b * w[1] / (c0 * w[0] + c1 * w[1]))
    high = max(1, min(high, (b - c0) // c1))
    equal = b // (2 * c0), b // (2 * c1)
    return {
        "width_proxy": prior.plan_units(b, request.costs, w),
        "variance": prior.variance_policy(request),
        "equal_spend": equal,
        "proportional": ((b - c1 * high) // c0, high),
        "minimax": prior.exact_variance(b, request.costs, w, 1, (0.25, 0.25)),
        "oracle": prior.exact_variance(b, request.costs, w, 1, tuple(p * (1 - p) for p in rates)),
        "direct": equal,
    }


def sensitivity_cell(settings, design, frozen):
    true_weights = settings["weights"]
    shift = settings["weight_high_shift"]
    weights = true_weights[0] - shift, true_weights[1] + shift
    rates = settings["rates"]
    mass = settings["mass"]
    truth = 0.3 + prior.SPAN * (
        (1 - mass) * sum(w * p for w, p in zip(true_weights, rates, strict=True))
        + mass * settings["hidden"]
    )
    cfg = {
        **frozen,
        "weights": weights,
        "alpha": settings["alpha"],
        "target_width": settings["width"],
    }
    costs = tuple(settings["tariffs"])
    size, total = settings["pilot"], settings["budget"]
    b = total - size * sum(costs)
    grouped = defaultdict(list)
    for i in range(design["replicates"]):
        seed = design["seed"], i
        hits = [
            int(np.count_nonzero(np.random.default_rng((*seed, 0, h)).random(size) < p))
            for h, p in enumerate(rates)
        ]
        hits[1] = min(size, round(hits[1] * settings["pilot_high_scale"]))
        request = prior.Request(b, costs, weights, 1, tuple(hits), size)
        allocation = sensitivity_allocation(request, rates)
        streams = [
            np.random.default_rng((*seed, 1, h)).random(max(a[h] for a in allocation.values())) < p
            for h, p in enumerate(rates)
        ]
        for units in allocation.values():
            prior.validate_allocation(request, units)
        allocation["abstain"] = (0, 0)
        for method, units in allocation.items():
            counts = tuple(
                int(np.count_nonzero(s[:n])) for s, n in zip(streams, units, strict=True)
            )
            result = prior.score(counts, units, settings, cfg, truth, method)
            grouped[method].append({**result, "n1": units[1]})
    summary = {}
    for method, rows in grouped.items():
        summary[method] = {
            "n": len(rows),
            "cost": 0 if method == "abstain" else total,
            "mean_n1": statistics.mean(r["n1"] for r in rows),
            "median_width": statistics.median(r["width"] for r in rows),
            **{
                key: sum(r[key] for r in rows)
                for key in (
                    "coverage",
                    "useful",
                    "abstention",
                    "wrong_call",
                    "certificate",
                    "false_certificate",
                    "utility",
                )
            },
        }
    return summary


def sensitivity(design, cfg):
    return {
        name: sensitivity_cell({**design["base"], **changes}, design, cfg)
        for name, changes in {"reference": {}, **design["variations"]}.items()
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("phase25_raw", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    require(
        all(prior.digest(PHASE / name) == digest for name, digest in FROZEN.items()),
        "Phase 26 freeze",
    )
    design = json.loads((PHASE / "design.json").read_text())
    _, cfg = prior.load_design()
    args.output.mkdir()
    prior.write_json(args.output / "reconstruction.json", reconstruction(args.phase25_raw))
    prior.write_json(args.output / "sensitivity.json", sensitivity(design, cfg))


if __name__ == "__main__":
    main()
