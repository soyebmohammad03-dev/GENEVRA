"""Independently verify Phase 25 costs, scoring, summaries and paired contrasts."""

import argparse
import csv
import hashlib
import json
import math
from collections import defaultdict
from pathlib import Path
from statistics import NormalDist, mean, median


def require(condition, label):
    if not condition:
        raise ValueError(f"verification failed: {label}")


def close(left, right):
    return math.isclose(left, right, rel_tol=0, abs_tol=1e-9)


def band(k, n, alpha):
    """Independent scalar inversion in log-likelihood units."""
    q = k / n
    peak = (k * math.log(q) if k else 0) + ((n - k) * math.log1p(-q) if k < n else 0)
    cutoff = peak + math.log(alpha / 4)

    def root(a, b, lower):
        for _ in range(58):
            p = (a + b) / 2
            if p in (0, 1):
                break
            lp = k * math.log(p) + (n - k) * math.log1p(-p)
            if (lp < cutoff) == lower:
                a = p
            else:
                b = p
        return (a + b) / 2

    return (root(0, q, True) if k else 0, root(q, 1, False) if k < n else 1)


def independent_bounds(counts, units, weights, case, alpha, method):
    if method == "abstain":
        return -240, 240
    first, second = (band(k, n, alpha) for k, n in zip(counts, units, strict=True))
    lo, hi = (weights[0] * first[i] + weights[1] * second[i] for i in (0, 1))
    if method != "direct":
        u = case["cap"]
        lo = (1 - u) * lo
        hi = max(hi, (1 - u) * hi + u * case["hidden_cap"])
    return 0.3 + 234.2 * lo, 0.3 + 234.2 * hi


def verify(directory):
    root = Path(__file__).resolve().parents[1]
    receipt = json.loads((directory / "receipt.json").read_text())
    cfg = json.loads((root / "docs/model_repair/phase_19/extension/config.json").read_text())
    phase = root / "docs/research/phase_25"
    design = json.loads((phase / "design.json").read_text())
    require(receipt["design"] == design, "design")
    hashes = {phase / name: digest for name, digest in receipt["freeze"].items()}
    hashes.update({directory / name: digest for name, digest in receipt["outputs"].items()})
    require(set(receipt["freeze"]) == {"PROTOCOL.md", "design.json"}, "freeze inventory")
    require(
        set(receipt["outputs"])
        == {"raw.csv", "results.json", "contrasts.csv", "allocation.png", "allocation.svg"},
        "output inventory",
    )
    hashes[root / "experiments/allocation_challenge.py"] = receipt["runner_sha256"]
    hashes[root / "src/genevra/analysis/coverage_envelope.py"] = receipt["inference_sha256"]
    hashes[root / "docs/model_repair/phase_19/extension/config.json"] = design[
        "phase19_config_sha256"
    ]
    for path, digest in hashes.items():
        require(hashlib.sha256(path.read_bytes()).hexdigest() == digest, str(path))
    cases = {r["name"]: r for r in cfg["cases"]}
    expected_methods = {
        "width_proxy",
        "variance",
        "minimax",
        "equal_spend",
        "proportional",
        "direct",
        "oracle",
        "abstain",
    }
    if receipt["entrant_sha256"]:
        expected_methods.add("entrant")
    samples, pilots = defaultdict(dict), {}
    prefixes = defaultdict(list)
    with (directory / "raw.csv").open(newline="") as f:
        for r in csv.DictReader(f):
            name, budget, method, i = r["case"], int(r["budget"]), r["method"], int(r["replicate"])
            case = cases[name]
            key = name, budget, method
            require(method in expected_methods and budget in cfg["budgets"], key)
            require(0 <= i < design["replicates"] and i not in samples[key], key)
            weights = cfg["weights"]
            p = (1 - case["mass"]) * sum(
                w * v for w, v in zip(weights, case["rates"], strict=True)
            ) + case["mass"] * case["hidden"]
            truth = 0.3 + 234.2 * p
            a, b, x, y = (int(r[k]) for k in ("n0", "n1", "k0", "k1"))
            cost = 0 if method == "abstain" else budget
            pilot_cost = design["pilot_per_stratum"] * case["block"] * sum(cfg["tariffs"])
            pilot = (r["pilot0"], r["pilot1"])
            if cost:
                require(0 <= x <= a and 0 <= y <= b and min(a, b) >= 1, key)
                require(pilot_cost + case["block"] * (a + 2 * b) == cost, key)
                require(all(0 <= int(k) <= design["pilot_per_stratum"] for k in pilot), key)
                pair_key = name, budget, i
                require(pilots.setdefault(pair_key, pilot) == pilot, pair_key)
                for stratum, prefix in enumerate(((a, x), (b, y))):
                    prefixes[name, budget, i, stratum].append(prefix)
                if method == "variance":
                    props = [(int(k) + 0.5) / (design["pilot_per_stratum"] + 1) for k in pilot]
                    coefficients = [
                        w * w * v * (1 - v) for w, v in zip(weights, props, strict=True)
                    ]
                    if i == 0:
                        unit_budget = (budget - pilot_cost) // case["block"]
                        brute = min(
                            coefficients[0] / (unit_budget - 2 * j) + coefficients[1] / j
                            for j in range(1, (unit_budget - 1) // 2 + 1)
                        )
                        require(close(brute, coefficients[0] / a + coefficients[1] / b), key)
            else:
                require((a, b, x, y, pilot) == (0, 0, 0, 0, ("", "")), key)
                pilot_cost = 0
            require(int(r["cost"]) == cost and int(r["pilot_cost"]) == pilot_cost, key)
            low, high = float(r["low"]), float(r["high"])
            require(-240 <= low <= high <= 240 and close(float(r["truth"]), truth), key)
            if i == 0:
                lo, hi = independent_bounds((x, y), (a, b), weights, case, cfg["alpha"], method)
                require(close(low, lo) and close(high, hi), (key, "independent band"))
            call = 1 if low > cfg["epsilon"] else -1 if high <= cfg["epsilon"] else 0
            cert = int(
                max(
                    abs(low - (0.3 + 234.2 * cfg["anchor"])),
                    abs(high - (0.3 + 234.2 * cfg["anchor"])),
                )
                <= cfg["tolerance"]
            )
            false = cert * (abs(p - cfg["anchor"]) * 234.2 > cfg["tolerance"])
            covered = int(low <= truth <= high)
            events = {
                "coverage": covered,
                "useful": covered * (high - low <= cfg["target_width"]),
                "abstention": int(not call),
                "wrong_call": int(bool(call) and call != (1 if truth > cfg["epsilon"] else -1)),
                "certificate": cert,
                "false_certificate": false,
            }
            require(int(r["call"]) == call and close(float(r["width"]), high - low), key)
            require(all(int(r[k]) == v for k, v in events.items()), key)
            require(int(r["utility"]) == cert - 2 * false, key)
            samples[key][i] = events, high - low, a, b, cert - 2 * false, cost, pilot_cost
    for key, counts in prefixes.items():
        counts.sort()
        require(
            all(
                0 <= next_k - k <= next_n - n
                for (n, k), (next_n, next_k) in zip(counts[:-1], counts[1:], strict=True)
            ),
            (key, "nested prefix counts"),
        )
    expected = {
        (case, budget, method)
        for case in cases
        for budget in cfg["budgets"]
        for method in expected_methods
    }
    require(set(samples) == expected, "cell inventory")
    results = json.loads((directory / "results.json").read_text())
    keys = [(r["case"], r["budget"], r["method"]) for r in results["summary"]]
    require(len(keys) == len(expected) and set(keys) == expected, "summary inventory")
    n = design["replicates"]
    z = NormalDist().inv_cdf(0.975)
    for key, row in zip(keys, results["summary"], strict=True):
        group = list(samples[key].values())
        require(len(group) == row["n"] == n, key)
        widths = sorted(r[1] for r in group)
        index = 0.9 * (n - 1)
        j = int(index)
        p90 = widths[j] + (index - j) * (widths[j + 1] - widths[j])
        for field, estimate in (
            ("mean_n0", mean(r[2] for r in group)),
            ("mean_n1", mean(r[3] for r in group)),
            ("median_width", median(widths)),
            ("p90_width", p90),
            ("utility", mean(r[4] for r in group)),
            ("cost", group[0][5]),
            ("pilot_cost", group[0][6]),
        ):
            require(close(row[field], estimate), (key, field))
        for event in group[0][0]:
            k = sum(r[0][event] for r in group)
            rate = row[event]
            midpoint = (k + z * z / 2) / (n + z * z)
            half = z * math.sqrt(k * (n - k) / n + z * z / 4) / (n + z * z)
            require(
                rate["count"] == k
                and close(rate["rate"], k / n)
                and close(rate["wilson"][0], max(0, midpoint - half))
                and close(rate["wilson"][1], min(1, midpoint + half)),
                (key, event),
            )
    contrast_keys = [(r["case"], r["budget"]) for r in results["contrasts"]]
    require(
        len(contrast_keys) == 18 and set(contrast_keys) == {(a, b) for a, b, _ in expected},
        "contrast inventory",
    )
    for (name, budget), row in zip(contrast_keys, results["contrasts"], strict=True):
        left, right = (samples[name, budget, m] for m in ("width_proxy", "variance"))
        estimate = mean(left[i][0]["useful"] - right[i][0]["useful"] for i in range(n))
        primary = (name, budget) == ("small_omission", 32768)
        alpha = design["comparative_alpha"] / (1 if primary else 17)
        half = math.sqrt(2 * math.log(2 / alpha) / n)
        low, high = max(-1, estimate - half), min(1, estimate + half)
        require(
            row["primary"] == primary
            and row["n"] == n
            and close(row["difference"], estimate)
            and close(row["low"], low)
            and close(row["high"], high)
            and row["clears_margin"] == (low > design["practical_margin"]),
            (name, budget),
        )
    print(f"Verified {len(samples) * n} replicate records, {len(keys)} cells and 18 contrasts")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    verify(parser.parse_args().output)
