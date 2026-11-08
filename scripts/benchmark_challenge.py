"""Replay the public benchmark or score a Phase 18 matched-package submission."""

import argparse
import csv
import json
import math
import os
import platform
import statistics
import subprocess
import sys
from pathlib import Path

import numpy as np
from replay_research import CATALOG, extract, sha

ROOT = Path(__file__).resolve().parents[1]
FIELDS = ("case", "replicate", "low", "high", "certificate")
ATOL = 1e-9
MATCHED_FIGURE_SHA256 = "bd2b3d0b53663c18b0ebe01a2b1c62597bca93dcc6ddc9ca30f2b424e7479c9b"
METHODS = ("combined", "direct", "stratified", "abstain", "pooled")


def compare(observed, expected, context):
    if not math.isclose(observed, expected, abs_tol=ATOL, rel_tol=0):
        raise ValueError(f"{context}: expected {expected}, got {observed}")


def interval_metrics(low, high, truth, certificate, anchor_error, epsilon, width, tolerance):
    """Score a declaration, retaining separate coverage and certificate endpoints."""
    if not (math.isfinite(low) and math.isfinite(high) and -240 <= low <= high <= 240):
        raise ValueError("invalid interval endpoints")
    if type(certificate) is not bool:
        raise ValueError("certificate must be Boolean")
    cover = low <= truth <= high
    call = 1 if low > epsilon else -1 if high <= epsilon else 0
    correct = call == (1 if truth > epsilon else -1)
    false = certificate and anchor_error > tolerance
    return {
        "coverage": cover,
        "coverage_decisive_correct": cover and correct,
        "precision": high - low <= width,
        "abstention": call == 0,
        "false_label": call != 0 and not correct,
        "certification": certificate,
        "false_certification": false,
    }


def rate(k, n):
    """Wilson descriptive interval, absent when the conditioning event never occurred."""
    if not 0 <= k <= n:
        raise ValueError("invalid binomial counts")
    if n == 0:
        return {"count": 0, "n": 0, "rate": None, "low": None, "high": None}
    z = statistics.NormalDist().inv_cdf(0.975)
    p = k / n
    denom = 1 + z**2 / n
    center = (p + z**2 / (2 * n)) / denom
    radius = z * math.sqrt(p * (1 - p) / n + z**2 / (4 * n**2)) / denom
    return {
        "count": k,
        "n": n,
        "rate": p,
        "low": max(0.0, center - radius),
        "high": min(1.0, center + radius),
    }


def load_submission(path, sizes):
    rows = {}
    with path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames != list(FIELDS):
            raise ValueError(f"expected CSV header {FIELDS}")
        for record in reader:
            if set(record) != set(FIELDS) or any(value is None for value in record.values()):
                raise ValueError("invalid CSV row")
            name = record["case"]
            token = record["replicate"]
            if name not in sizes or not token.isascii() or not token.isdecimal():
                raise ValueError("unexpected case or replicate")
            replicate = int(token)
            key = (name, replicate)
            if not 0 <= replicate < sizes[name] or key in rows:
                raise ValueError(f"out-of-range or duplicate key {key}")
            flag = record["certificate"]
            if flag not in {"0", "1"}:
                raise ValueError(f"invalid certificate flag for {key}")
            rows[key] = (float(record["low"]), float(record["high"]), flag == "1")
    if len(rows) != sum(sizes.values()):
        raise ValueError("submission must contain every expected replicate")
    return rows


def evaluate(rows, observations, cfg):
    """Score per case. Paired utility is +1 correct, -1 false, 0 no certificate."""
    cases, utility = {}, {}
    for name, (truth, errors) in observations.items():
        metrics, widths, values = [], [], []
        for j, error in enumerate(errors):
            low, high, certificate = rows[name, j]
            events = interval_metrics(
                low,
                high,
                truth,
                certificate,
                error,
                cfg["epsilon"],
                cfg["width_target"],
                cfg["transfer_tolerance"],
            )
            metrics.append(events)
            widths.append(high - low)
            values.append(int(certificate) - 2 * int(events["false_certification"]))
        n = len(metrics)
        counts = {key: sum(row[key] for row in metrics) for key in metrics[0]}
        issued = counts["certification"]
        decisive = n - counts["abstention"]
        cases[name] = {
            "rates": {key: rate(count, n) for key, count in counts.items()}
            | {
                "false_among_certified": rate(counts["false_certification"], issued),
                "coverage_given_decision": rate(counts["coverage_decisive_correct"], decisive),
                "coverage_given_certificate": rate(
                    sum(row["coverage"] and row["certification"] for row in metrics), issued
                ),
            },
            "median_width": statistics.median(widths),
            "p90_width": statistics.quantiles(widths, n=10, method="inclusive")[-1],
        }
        utility[name] = values
    return cases, utility


def paired(candidate, baseline, cases, alpha):
    differences = []
    n = len(candidate[cases[0]])
    for case in cases:
        left, right = candidate[case], baseline[case]
        if len(left) != n or len(right) != n:
            raise ValueError("unbalanced paired primary design")
        differences.extend(a - b for a, b in zip(left, right, strict=True))
    delta = statistics.mean(differences)
    radius = math.sqrt(8 * math.log(2 / alpha) / len(differences))
    return {
        "difference": delta,
        "low": max(-2, delta - radius),
        "high": min(2, delta + radius),
        "n": len(differences),
    }


def phase18_inputs(archive):
    root = archive / "phase-18"
    cfg = json.loads((root / "docs/model_repair/phase_18/config.json").read_text())
    observations, public_inputs = {}, {}
    for i, case in enumerate(cfg["cases"]):
        name = case["name"]
        payload = json.loads((root / f"raw/cells/{i}.json").read_text())["payload"]
        if payload["key"] != [i] or len(payload["source_tail"]) != cfg["replicates"]:
            raise ValueError(f"wrong input identity for {name}")
        p = math.fsum(((1 - case["weight"]) * 0.0002, case["weight"] * case["target_high"]))
        truth = 0.3 + 234.2 * p
        errors = [234.2 * abs(k / cfg["source_rows"] - p) for k in payload["source_tail"]]
        observations[name] = truth, errors
        public_inputs[name] = {
            "design": {k: case[k] for k in ("regime", "weight", "block", "missing")},
            "counts": {k: v for k, v in payload.items() if k not in {"key", "seeds"}},
        }
    return cfg, observations, public_inputs


def baseline_rows(arrays, cfg, method):
    rows = {}
    for case in cfg["cases"]:
        if method == "pooled" and case["regime"] != "registered":
            continue
        name = case["name"]
        prefix = f"{name}_{method}"
        bounds, cert = arrays[f"{prefix}_interval"], arrays[f"{prefix}_cert"]
        if bounds.shape != (cfg["replicates"], 2) or cert.shape != (cfg["replicates"],):
            raise ValueError(f"wrong baseline array shape for {prefix}")
        if cert.dtype != np.dtype(bool):
            raise ValueError(f"non-Boolean baseline flags for {prefix}")
        for j, ((lo, hi), issued) in enumerate(zip(bounds, cert, strict=True)):
            rows[name, j] = (float(lo), float(hi), bool(issued))
    return rows


def read_csv(path):
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def verify_baselines(results, cfg, observations):
    metrics, utilities = {}, {}
    with np.load(results / "replicates.npz", allow_pickle=False) as arrays:
        for method in METHODS:
            rows = baseline_rows(arrays, cfg, method)
            subset = {name: obs for name, obs in observations.items() if (name, 0) in rows}
            metrics[method], utilities[method] = evaluate(rows, subset, cfg)
    for row in read_csv(results / "rates.csv"):
        key = row["metric"]
        if key == "admission":
            continue  # Legacy raw verifier independently checks admission.
        result = metrics[row["method"]][row["case"]]["rates"][key]
        if (result["count"], result["n"]) != (int(row["count"]), int(row["n"])):
            raise ValueError(f"wrong published count for {row}")
        for field in ("rate", "low", "high"):
            compare(result[field], float(row[field]), row)
    for row in read_csv(results / "summary.csv"):
        if row["available"] == "True":
            for key in ("median_width", "p90_width"):
                compare(metrics[row["method"]][row["case"]][key], float(row[key]), row)
    contrasts = {}
    for row in read_csv(results / "primary.csv"):
        method = row["comparator"]
        contrast = paired(utilities["combined"], utilities[method], cfg["primary_cases"], 0.05 / 3)
        for key in ("difference", "low", "high"):
            compare(contrast[key], float(row[key]), row)
        contrasts[method] = contrast
    return metrics, contrasts


def write_json(path, payload):
    with path.open("x", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, allow_nan=False)
        handle.write("\n")


def regenerate_notebook(output):
    import nbformat
    from nbclient import NotebookClient

    os.environ["GENEVRA_REPLAY"] = str(output)
    os.environ["GENEVRA_NOTEBOOK_FIGURES"] = str(output)
    book = nbformat.read(ROOT / "notebooks/certification_evidence.ipynb", as_version=4)
    nbformat.validate(book)
    execution = NotebookClient(book, timeout=60, kernel_name="python3").execute(cwd=str(ROOT))
    nbformat.write(execution, output / "executed.ipynb")


def adversarial_replay(output, combined):
    """Lock representative counterexamples after their raw-data checks pass."""
    observed = {
        "matched_coverage": combined["registered_matched"]["rates"]["coverage"]["count"],
        "shared_blind_false_certificates": (
            combined["shared_blind"]["rates"]["false_certification"]["count"]
        ),
        "shared_blind_coverage": combined["shared_blind"]["rates"]["coverage"]["count"],
        "frame_stale_abstentions": combined["frame_stale"]["rates"]["abstention"]["count"],
        "audit_stale_abstentions": combined["audit_stale"]["rates"]["abstention"]["count"],
        "missing_stratum_abstentions": combined["missing_stratum"]["rates"]["abstention"]["count"],
        "near_threshold_abstentions": combined["near_threshold"]["rates"]["abstention"]["count"],
    }
    ext = json.loads((output / "phase-19-extension/results.json").read_text())["summary"]
    extension = {(r["case"], r["method"]): r for r in ext if r["budget"] == 32768}
    for case, method in (
        ("large_omission", "reachable_only"),
        ("large_omission", "equal_envelope"),
        ("bad_mass_cap", "equal_envelope"),
        ("bad_hidden_support", "equal_envelope"),
        ("duplicates", "equal_envelope"),
    ):
        observed[f"{case}/{method}/coverage"] = extension[case, method]["rates"]["coverage"][
            "count"
        ]
    wrong_weight = next(
        row
        for row in read_csv(output / "phase-15/certificates.csv")
        if (row["scenario"], row["metric"]) == ("wrong_weight", "false_certificate")
    )
    observed["wrong_weight_false_certificates"] = int(wrong_weight["count"])
    expected = {
        "wrong_weight_false_certificates": 485,
        "matched_coverage": 512,
        "shared_blind_false_certificates": 180,
        "shared_blind_coverage": 0,
        "frame_stale_abstentions": 512,
        "audit_stale_abstentions": 512,
        "missing_stratum_abstentions": 512,
        "near_threshold_abstentions": 512,
        "large_omission/reachable_only/coverage": 0,
        "large_omission/equal_envelope/coverage": 512,
        "bad_mass_cap/equal_envelope/coverage": 0,
        "bad_hidden_support/equal_envelope/coverage": 0,
        "duplicates/equal_envelope/coverage": 512,
    }
    if observed != expected:
        raise ValueError(f"adversarial replay mismatch: {observed}")
    return observed


def run_reproduction(output, archive):
    command = [sys.executable, str(ROOT / "scripts/replay_research.py"), "--output", str(output)]
    if archive:
        command += ["--archive", str(archive)]
    subprocess.run(command, check=True, cwd=ROOT)
    cfg, observations, _ = phase18_inputs(output / "archive")
    metrics, contrasts = verify_baselines(output / "phase-18", cfg, observations)
    ext = ROOT / "docs/model_repair/phase_19/extension"
    subprocess.run(
        [
            sys.executable,
            str(ext / "plot.py"),
            str(output / "phase-19-extension/results.json"),
            str(output / "coverage_envelope"),
        ],
        check=True,
        cwd=ROOT,
    )
    regenerate_notebook(output)
    figures = {
        "phase-18/matched_access.png": MATCHED_FIGURE_SHA256,
        "coverage_envelope.svg": sha(ext / "coverage_envelope.svg"),
        "identification_floor.png": sha(ROOT / "docs/research/identification_floor.png"),
    }
    for name, expected in figures.items():
        if sha(output / name) != expected:
            raise ValueError(f"figure SHA-256 mismatch: {name}")
    write_json(
        output / "challenge-verification.json",
        {
            "schema": "genevra-challenge-v1",
            "status": "passed",
            "archive": json.loads((output / "receipt.json").read_text()),
            "platform": platform.platform(),
            "python": sys.version,
            "verifier_sha256": sha(Path(__file__)),
            "absolute_tolerance": ATOL,
            "figure_sha256": figures,
            "adversarial_replay_counts": adversarial_replay(output, metrics["combined"]),
            "phase18_metrics": metrics,
            "phase18_primary_contrasts": contrasts,
            "phase19_extension_primary": json.loads(
                (output / "phase-19-extension/results.json").read_text()
            )["primary"],
        },
    )


def run_submission(args):
    cfg, observations, public_inputs = phase18_inputs(args.output / "archive")
    if args.action == "prepare":
        shared = {
            k: cfg[k]
            for k in (
                "version",
                "replicates",
                "target_rows_per_stream",
                "source_rows",
                "body_draws",
                "tail_draws",
                "epsilon",
                "width_target",
                "transfer_tolerance",
                "alpha",
            )
        }
        write_json(
            args.output / "acquisition-package.json",
            {
                "schema": "genevra-phase18-acquisition-v1",
                "settings": shared,
                "cases": public_inputs,
            },
        )
        return
    rows = load_submission(args.submission, {name: len(v[1]) for name, v in observations.items()})
    metrics, utilities = evaluate(rows, observations, cfg)
    with np.load(args.output / "archive/phase-18/results/replicates.npz", allow_pickle=False) as a:
        _, baseline = evaluate(baseline_rows(a, cfg, "combined"), observations, cfg)
    write_json(
        args.output / "submission-score.json",
        {
            "schema": "genevra-challenge-v1",
            "submission_sha256": sha(args.submission),
            "archive_sha256": json.loads(CATALOG.read_text())["sha256"],
            "metrics": metrics,
            "exploratory_paired_vs_combined": paired(
                utilities, baseline, cfg["primary_cases"], 0.05
            ),
        },
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    actions = parser.add_subparsers(dest="action", required=True)
    for name in ("reproduce", "prepare", "score"):
        action = actions.add_parser(name)
        action.add_argument("--output", required=True, type=Path, help="new output directory")
        action.add_argument(
            "--archive",
            type=Path,
            required=name != "reproduce",
            help="verified public capsule; optional download for reproduce",
        )
        if name == "score":
            action.add_argument("--submission", required=True, type=Path)
    args = parser.parse_args()
    args.output = args.output.resolve()
    os.environ.setdefault("MPLBACKEND", "Agg")
    if args.action == "reproduce":
        run_reproduction(args.output, args.archive)
    else:
        args.output.mkdir()
        extract(args.archive, args.output / "archive", json.loads(CATALOG.read_text())["sha256"])
        run_submission(args)


if __name__ == "__main__":
    main()
