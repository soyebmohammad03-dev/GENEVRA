"""Run or reconstruct the frozen coverage-envelope benchmark."""

import argparse
import hashlib
import json
import math
import platform
import sys
from pathlib import Path
from statistics import NormalDist
from typing import Any

import numpy as np

from genevra.analysis.coverage_envelope import (
    CoverageEnvelope,
    ScoreDecision,
    plan_units,
    reachable_band,
    score_decision,
)

FROZEN = {
    "config.json": "e41d0c223d8e6cd4b5d109e488270b18a61e71640d32da8e6fd41c6d1c40fb3a",
    "EXPERIMENT_PROTOCOL.md": ("3e94f543344ee1f62cedc49c4eebd1bff958a3023ec740f971ae518374e4bef7"),
}
BODY, TAIL = 0.3, 234.5


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def encode(value: Any) -> str:
    return json.dumps(value, sort_keys=True, allow_nan=False, indent=2) + "\n"


def write_once(path: Path, value: Any) -> None:
    with path.open("x") as handle:
        handle.write(encode(value))


def allocation(
    cfg: dict[str, Any], case: dict[str, Any], budget: int
) -> dict[str, tuple[int, int]]:
    block = case["block"]
    tariffs = (cfg["tariffs"][0] * block, cfg["tariffs"][1] * block)
    equal = (budget // (2 * tariffs[0]), budget // (2 * tariffs[1]))
    planned = plan_units(budget, tariffs, tuple(cfg["weights"]))
    for units in (equal, planned):
        if sum(n * c for n, c in zip(units, tariffs, strict=True)) != budget:
            raise ValueError("allocation did not exhaust the matched budget")
    return {"equal": equal, "planned": planned}


def generate(cfg: dict[str, Any], index: int, budget_index: int) -> dict[str, Any]:
    case = cfg["cases"][index]
    budget = cfg["budgets"][budget_index]
    units = allocation(cfg, case, budget)
    n = cfg["replicates"]
    streams = [[cfg["seed"], index, budget_index, h] for h in range(2)]
    counts: dict[str, list[list[int]]] = {"equal": [], "planned": []}
    for h, rate in enumerate(case["rates"]):
        generator = np.random.default_rng(streams[h])
        low, high = sorted((units["equal"][h], units["planned"][h]))
        common = generator.binomial(low, rate, n)
        extra = generator.binomial(high - low, rate, n)
        for key, size in units.items():
            counts[key].append((common if size[h] == low else common + extra).tolist())
    return {
        "case": case["name"],
        "budget": budget,
        "block": case["block"],
        "seeds": streams,
        "units": {name: list(size) for name, size in units.items()},
        "counts_by_stratum": counts,
    }


def proportion(k: int, n: int) -> dict[str, Any]:
    p = k / n
    z = NormalDist().inv_cdf(0.975)
    denominator = 1 + z * z / n
    center = (p + z * z / (2 * n)) / denominator
    radius = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denominator
    return {
        "count": k,
        "n": n,
        "rate": p,
        "wilson": [max(0, center - radius), min(1, center + radius)],
    }


def analyze(cfg: dict[str, Any], records: list[dict[str, Any]]) -> dict[str, Any]:
    weights = (cfg["weights"][0], cfg["weights"][1])
    eps, tolerance, anchor = (cfg[k] for k in ("epsilon", "tolerance", "anchor"))
    n = cfg["replicates"]
    summary = []
    primary: dict[str, Any] = {}
    for record in records:
        case = next(c for c in cfg["cases"] if c["name"] == record["case"])
        budget = record["budget"]
        reachable = sum(w * r for w, r in zip(weights, case["rates"], strict=True))
        p = (1 - case["mass"]) * reachable + case["mass"] * case["hidden"]
        truth = BODY + (TAIL - BODY) * p
        false = abs((TAIL - BODY) * (p - anchor)) > tolerance
        envelope = CoverageEnvelope((0, case["cap"]), (0, case["hidden_cap"]))
        unrestricted = CoverageEnvelope((0, case["cap"]), (0, 1))
        decisions: dict[str, list[ScoreDecision]] = {
            key: []
            for key in (
                "reachable_only",
                "equal_envelope",
                "planned_envelope",
                "full_hidden_support",
                "abstain",
            )
        }
        for i in range(n):
            bands = {}
            for key in ("equal", "planned"):
                a, b = record["counts_by_stratum"][key]
                x, y = record["units"][key]
                bands[key] = reachable_band((a[i], b[i]), (x, y), weights, cfg["alpha"])
            tails = {
                "reachable_only": bands["equal"],
                "equal_envelope": envelope.target_tail(bands["equal"]),
                "planned_envelope": envelope.target_tail(bands["planned"]),
                "full_hidden_support": unrestricted.target_tail(bands["planned"]),
            }
            for key, tail in tails.items():
                decisions[key].append(score_decision(tail, BODY, TAIL, anchor, eps, tolerance))
            decisions["abstain"].append(ScoreDecision((-240, 240), 0, False))
        precision_coverage = {}
        for key, values in decisions.items():
            lo, hi = np.asarray([v.bounds for v in values]).T
            cert = np.asarray([v.certified for v in values])
            call = np.asarray([v.call for v in values])
            cover = (lo <= truth) & (truth <= hi)
            precision = hi - lo <= cfg["target_width"]
            precision_coverage[key] = precision & cover
            metrics = {
                "coverage": cover,
                "precision": precision,
                "coverage_with_precision": cover & precision,
                "correct_decisive_coverage": cover & (call == (1 if truth > eps else -1)),
                "abstention": call == 0,
                "certificate": cert,
                "false_certificate": cert & false,
            }
            size = record["units"][
                "planned" if key in ("planned_envelope", "full_hidden_support") else "equal"
            ]
            oracle = envelope.target_tail((reachable, reachable))
            summary.append(
                {
                    "case": record["case"],
                    "budget": budget,
                    "method": key,
                    "truth": truth,
                    "acquisition_cost": budget if key != "abstain" else 0,
                    "independent_units": size if key != "abstain" else [0, 0],
                    "charged_rows": sum(size) * record["block"] if key != "abstain" else 0,
                    "oracle_width": (TAIL - BODY) * (oracle[1] - oracle[0]),
                    "median_width": float(np.median(hi - lo)),
                    "p90_width": float(np.quantile(hi - lo, 0.9)),
                    "rates": {
                        name: proportion(int(mask.sum()), n) for name, mask in metrics.items()
                    },
                }
            )
        if record["case"] == "small_omission" and budget == 32768:
            diff = (
                precision_coverage["planned_envelope"].astype(int)
                - precision_coverage["equal_envelope"]
            )
            gain = float(diff.mean())
            radius = math.sqrt(2 * math.log(40) / n)
            primary = {
                "difference": gain,
                "interval": [max(-1, gain - radius), min(1, gain + radius)],
                "passes": gain - radius > 0.05,
                "n": n,
            }
        print(f"verified analysis {record['case']} budget={budget}", flush=True)
    return {"summary": summary, "primary": primary, "replicates": len(records) * n}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("acquire", "analyze"))
    parser.add_argument("protocol", type=Path)
    parser.add_argument("raw", type=Path)
    parser.add_argument("results", type=Path)
    args = parser.parse_args()
    if args.results.exists():
        raise FileExistsError("result destination already exists")
    if any(sha(args.protocol / name) != value for name, value in FROZEN.items()):
        raise ValueError("frozen protocol or configuration changed")
    cfg = json.loads((args.protocol / "config.json").read_text())
    records = [
        generate(cfg, i, j) for i in range(len(cfg["cases"])) for j in range(len(cfg["budgets"]))
    ]
    base = Path(__file__).resolve().parents[1]
    identity = {
        "freeze": FROZEN,
        "runner_sha256": sha(Path(__file__)),
        "analysis_sha256": sha(base / "src/genevra/analysis/coverage_envelope.py"),
        "numpy": np.__version__,
        "python": platform.python_version(),
    }
    if args.mode == "acquire":
        write_once(args.raw, {"identity": identity, "records": records})
    actual = json.loads(args.raw.read_text())
    if actual != {"identity": identity, "records": records}:
        raise ValueError("raw observations or provenance differ from deterministic design")
    write_once(args.results, analyze(cfg, actual["records"]))
    print(f"Python {sys.version.split()[0]} / NumPy {np.__version__}", flush=True)


if __name__ == "__main__":
    main()
