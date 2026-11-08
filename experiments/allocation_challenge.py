"""Run the bounded Phase 25 comparative allocation benchmark."""

import argparse
import csv
import hashlib
import importlib.util
import json
import math
import platform
from collections import defaultdict
from functools import lru_cache
from pathlib import Path
from typing import NamedTuple

import numpy as np

from genevra.analysis.coverage_envelope import (
    CoverageEnvelope,
    plan_units,
    reachable_band,
    score_decision,
)

ROOT = Path(__file__).resolve().parents[1]
PHASE = ROOT / "docs/research/phase_25"
SPAN = 234.2
MATCHED = ("width_proxy", "variance", "minimax", "equal_spend", "proportional", "direct")
FROZEN = {
    "PROTOCOL.md": "148376915f48caaeb8e58708d7106ea6ff731a6a80fa393dbe153406018d7fdc",
    "design.json": "4f99125ba7902a73a1f0cc97414ec1234f653b14c8fc7c45300e9d9d9132c8a8",
}


class Request(NamedTuple):
    budget: int
    costs: tuple[int, int]
    weights: tuple[float, float]
    minimum: int
    pilot_hits: tuple[int, int]
    pilot_n: int


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path, data):
    with path.open("x", encoding="utf-8") as f:
        json.dump(data, f, indent=2, allow_nan=False)
        f.write("\n")


def load_design():
    if any(digest(PHASE / name) != expected for name, expected in FROZEN.items()):
        raise ValueError("Phase 25 freeze mismatch")
    design = json.loads((PHASE / "design.json").read_text())
    cfg_path = ROOT / "docs/model_repair/phase_19/extension/config.json"
    if digest(cfg_path) != design["phase19_config_sha256"]:
        raise ValueError("frozen Phase 19 configuration mismatch")
    return design, json.loads(cfg_path.read_text())


def validate_request(r):
    if (
        len(r.costs) != 2
        or any(type(c) is not int or c <= 0 for c in r.costs)
        or type(r.budget) is not int
        or type(r.minimum) is not int
        or r.minimum < 1
        or r.budget < r.minimum * sum(r.costs)
        or len(r.weights) != 2
        or any(not 0 < w < 1 for w in r.weights)
        or not math.isclose(sum(r.weights), 1, rel_tol=0, abs_tol=1e-12)
        or type(r.pilot_n) is not int
        or r.pilot_n < 1
        or len(r.pilot_hits) != 2
        or any(type(k) is not int or not 0 <= k <= r.pilot_n for k in r.pilot_hits)
    ):
        raise ValueError("invalid or missing budget, stratum, or pilot information")


def validate_allocation(r, counts):
    if len(counts) != 2 or any(type(n) is not int or n < r.minimum for n in counts):
        raise ValueError("allocation needs two integer counts above the minimum")
    if sum(n * c for n, c in zip(counts, r.costs, strict=True)) != r.budget:
        raise ValueError("allocation must spend the exact remaining budget")


@lru_cache(maxsize=512)
def exact_variance(budget, costs, weights, minimum, variances):
    """Minimize sum(w² v/n) over feasible exact-spend integer pairs."""
    if any(not 0 <= v <= 0.25 for v in variances):
        raise ValueError("invalid Bernoulli variance")
    high = np.arange(minimum, (budget - costs[0] * minimum) // costs[1] + 1)
    remaining = budget - costs[1] * high
    eligible = remaining % costs[0] == 0
    high, low = high[eligible], remaining[eligible] // costs[0]
    if not len(high):
        raise ValueError("no exact-spend allocation")
    j = int(np.argmin(weights[0] ** 2 * variances[0] / low + weights[1] ** 2 * variances[1] / high))
    return int(low[j]), int(high[j])


def variance_policy(request):
    """Example entrant. The request exposes only operational allocation inputs."""
    validate_request(request)
    p = tuple((k + 0.5) / (request.pilot_n + 1) for k in request.pilot_hits)
    return exact_variance(
        request.budget,
        request.costs,
        request.weights,
        request.minimum,
        tuple(x * (1 - x) for x in p),
    )


def plans(r):
    validate_request(r)
    if r.minimum != 1 or r.costs[1] != 2 * r.costs[0]:
        raise ValueError("fixed benchmark policies require the frozen tariff ratio and minimum")
    b, c, w, m = r.budget, r.costs, r.weights, r.minimum
    equal = (b // (2 * c[0]), b // (2 * c[1]))
    high = round(b * w[1] / sum(a * z for a, z in zip(c, w, strict=True)))
    high = min(max(high, m), (b - c[0] * m) // c[1])
    return {
        "width_proxy": plan_units(b, c, w),
        "variance": variance_policy(r),
        "minimax": exact_variance(b, c, w, m, (0.25, 0.25)),
        "equal_spend": equal,
        "proportional": ((b - c[1] * high) // c[0], high),
        "direct": equal,
    }


def observations(seed, index, budget_index, replicate, case, total, cfg, design, entrant):
    size = design["pilot_per_stratum"]
    costs = tuple(c * case["block"] for c in cfg["tariffs"])
    weights = tuple(cfg["weights"])
    pilot_cost = size * sum(costs)
    key = (seed, index, budget_index, replicate)
    pilot_rng = np.random.default_rng((*key, 0))
    pilot = tuple(map(int, pilot_rng.binomial(size, case["rates"])))
    request = Request(
        total - pilot_cost, costs, weights, design["minimum_per_stratum"], pilot, size
    )
    allocations = plans(request)
    if entrant is not None:
        allocations["entrant"] = entrant(request)
    # Oracle decisions are reported separately from the matched information comparisons.
    allocations["oracle"] = exact_variance(
        request.budget,
        costs,
        weights,
        request.minimum,
        tuple(p * (1 - p) for p in case["rates"]),
    )
    for allocation in allocations.values():
        validate_allocation(request, allocation)
    samples = [
        np.random.default_rng((*key, 1, h)).random(max(a[h] for a in allocations.values())) < rate
        for h, rate in enumerate(case["rates"])
    ]
    counts = {
        name: tuple(int(np.count_nonzero(samples[h][:n])) for h, n in enumerate(units))
        for name, units in allocations.items()
    }
    return request, pilot_cost, allocations, counts


def wilson(k, n):
    z = 1.959963984540054
    p = k / n
    d = 1 + z**2 / n
    mid = (p + z**2 / (2 * n)) / d
    radius = z * math.sqrt(p * (1 - p) / n + z**2 / (4 * n**2)) / d
    return [max(0.0, mid - radius), min(1.0, mid + radius)]


def score(counts, units, case, cfg, truth, method):
    if method == "abstain":
        low, high, call, cert = -240.0, 240.0, 0, False
    else:
        band = reachable_band(counts, units, tuple(cfg["weights"]), cfg["alpha"])
        if method != "direct":
            band = CoverageEnvelope((0, case["cap"]), (0, case["hidden_cap"])).target_tail(band)
        result = score_decision(band, 0.3, 234.5, cfg["anchor"], cfg["epsilon"], cfg["tolerance"])
        (low, high), call, cert = result.bounds, result.call, result.certified
    false = cert and abs(truth - (0.3 + SPAN * cfg["anchor"])) > cfg["tolerance"]
    cover = low <= truth <= high
    return {
        "low": low,
        "high": high,
        "call": call,
        "width": high - low,
        "coverage": int(cover),
        "useful": int(cover and high - low <= cfg["target_width"]),
        "abstention": int(call == 0),
        "wrong_call": int(call != 0 and call != (1 if truth > cfg["epsilon"] else -1)),
        "certificate": int(cert),
        "false_certificate": int(false),
        "utility": int(cert) - 2 * int(false),
    }


def paired(differences, alpha):
    gain = float(np.mean(differences))
    radius = math.sqrt(2 * math.log(2 / alpha) / len(differences))
    return gain, max(-1.0, gain - radius), min(1.0, gain + radius)


def run(design, cfg, output, entrant):
    output.mkdir()
    summary, contrasts = [], []
    with (output / "raw.csv").open("x", newline="", encoding="utf-8") as stream:
        writer = None
        for i, case in enumerate(cfg["cases"]):
            p = sum(w * v for w, v in zip(cfg["weights"], case["rates"], strict=True))
            truth = 0.3 + SPAN * ((1 - case["mass"]) * p + case["mass"] * case["hidden"])
            for j, budget in enumerate(cfg["budgets"]):
                grouped = defaultdict(list)
                for replicate in range(design["replicates"]):
                    request, pilot_cost, allocation, counts = observations(
                        design["seed"], i, j, replicate, case, budget, cfg, design, entrant
                    )
                    allocation["abstain"] = counts["abstain"] = (0, 0)
                    for method, units in allocation.items():
                        paid = method != "abstain"
                        hits = counts[method]
                        result = score(hits, units, case, cfg, truth, method)
                        record = {
                            "case": case["name"],
                            "budget": budget,
                            "replicate": replicate,
                            "method": method,
                            "truth": truth,
                            "pilot0": request.pilot_hits[0] if paid else "",
                            "pilot1": request.pilot_hits[1] if paid else "",
                            "pilot_cost": pilot_cost if paid else 0,
                            "cost": budget if paid else 0,
                            "n0": units[0],
                            "n1": units[1],
                            "k0": hits[0],
                            "k1": hits[1],
                            **result,
                        }
                        if writer is None:
                            writer = csv.DictWriter(
                                stream, fieldnames=list(record), lineterminator="\n"
                            )
                            writer.writeheader()
                        writer.writerow(record)
                        grouped[method].append(record)
                n = design["replicates"]
                for method, rows in grouped.items():
                    summary.append(
                        {
                            "case": case["name"],
                            "budget": budget,
                            "method": method,
                            "n": n,
                            "information": "oracle"
                            if method == "oracle"
                            else "no_acquisition"
                            if method == "abstain"
                            else "matched",
                            "cost": rows[0]["cost"],
                            "pilot_cost": rows[0]["pilot_cost"],
                            "mean_n0": float(np.mean([r["n0"] for r in rows])),
                            "mean_n1": float(np.mean([r["n1"] for r in rows])),
                            "median_width": float(np.median([r["width"] for r in rows])),
                            "p90_width": float(np.quantile([r["width"] for r in rows], 0.9)),
                            "utility": float(np.mean([r["utility"] for r in rows])),
                            **{
                                key: {
                                    "count": k,
                                    "rate": k / n,
                                    "wilson": wilson(k, n),
                                }
                                for key in (
                                    "coverage",
                                    "useful",
                                    "abstention",
                                    "wrong_call",
                                    "certificate",
                                    "false_certificate",
                                )
                                for k in [sum(r[key] for r in rows)]
                            },
                        }
                    )
                primary = case["name"] == "small_omission" and budget == 32768
                alpha = design["comparative_alpha"] / (1 if primary else 17)
                gain, low, high = paired(
                    [
                        a["useful"] - b["useful"]
                        for a, b in zip(grouped["width_proxy"], grouped["variance"], strict=True)
                    ],
                    alpha,
                )
                contrasts.append(
                    {
                        "case": case["name"],
                        "budget": budget,
                        "primary": primary,
                        "n": n,
                        "difference": gain,
                        "low": low,
                        "high": high,
                        "clears_margin": low > design["practical_margin"],
                    }
                )
    write_json(output / "results.json", {"summary": summary, "contrasts": contrasts})
    with (output / "contrasts.csv").open("x", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(contrasts[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(contrasts)


def plot(output):
    import matplotlib

    matplotlib.use("Agg")
    from matplotlib import pyplot as plt

    plt.rcParams["svg.hashsalt"] = "genevra-phase25-v1"
    rows = json.loads((output / "results.json").read_text())["contrasts"]
    fig, axes = plt.subplots(1, 2, sharey=True, figsize=(10, 5), layout="constrained")
    for ax, budget in zip(axes, (8192, 32768), strict=True):
        group = [r for r in rows if r["budget"] == budget]
        for y, row in enumerate(group):
            color = "#8f3a22" if row["primary"] else "#176c76"
            ax.hlines(y, row["low"], row["high"], color=color, linewidth=2)
            ax.scatter(row["difference"], y, color=color, s=18)
        ax.set_yticks(range(len(group)), [r["case"].replace("_", " ") for r in group])
        ax.axvline(0, color="0.35", linewidth=0.8)
        ax.axvline(0.05, color="0.65", linestyle=":", linewidth=1)
        ax.set_title(f"{budget:,} charged units")
        ax.set_xlim(-1, 1)
    fig.supxlabel("Covered-and-precise probability difference (width proxy − variance)")
    fig.suptitle("Phase 25 matched allocation on public synthetic laws")
    svg = output / "allocation.svg"
    fig.savefig(svg, metadata={"Date": None})
    svg.write_text("\n".join(line.rstrip() for line in svg.read_text().splitlines()) + "\n")
    fig.savefig(output / "allocation.png", dpi=220)
    plt.close(fig)


def load_entrant(path):
    spec = importlib.util.spec_from_file_location("phase25_entrant", path)
    if spec is None or spec.loader is None:
        raise ValueError("expected an importable entrant .py file")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.allocate


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--entrant", type=Path, help="trusted Python module with allocate(request)")
    args = parser.parse_args()
    design, cfg = load_design()
    entrant = load_entrant(args.entrant) if args.entrant else None
    run(design, cfg, args.output, entrant)
    plot(args.output)
    files = sorted(args.output.iterdir())
    write_json(
        args.output / "receipt.json",
        {
            "design": design,
            "freeze": FROZEN,
            "runner_sha256": digest(Path(__file__)),
            "inference_sha256": digest(ROOT / "src/genevra/analysis/coverage_envelope.py"),
            "entrant_sha256": digest(args.entrant) if args.entrant else None,
            "python": platform.python_version(),
            "numpy": np.__version__,
            "outputs": {p.name: digest(p) for p in files},
        },
    )


if __name__ == "__main__":
    main()
