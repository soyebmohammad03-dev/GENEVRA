"""Audit the frozen GENEVRA evidence and render the final review manuscript."""

import argparse
import csv
import json
import math
import re
from collections import defaultdict
from pathlib import Path
from statistics import mean

import benchmark_reference as ref
import build_publication as publication

ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / "docs/research/phase_29"
PHASE28 = ROOT / "docs/research/phase_28"
EXTENSION = ROOT / "docs/model_repair/phase_19/extension"
SCORE_SPAN = 234.2


def check_width_records(raw, data):
    """Recalculate components and classify each matched primary observation."""
    cfg = json.loads((EXTENSION / "config.json").read_text())
    methods = publication.METHODS
    case = next(c for c in cfg["cases"] if c["name"] == "small_omission")
    weights = cfg["weights"]
    groups = defaultdict(dict)
    with raw.open(newline="", encoding="utf-8") as stream:
        for row in csv.DictReader(stream):
            method = row["method"]
            if (row["case"], row["budget"]) != ("small_omission", "32768") or method not in methods:
                continue
            units = [int(row[f"n{i}"]) for i in (0, 1)]
            hits = [int(row[f"k{i}"]) for i in (0, 1)]
            bounds = [
                ref.bernoulli_limits(k, n, cfg["alpha"]) for k, n in zip(hits, units, strict=True)
            ]
            low, high = [
                math.fsum(w * b[j] for w, b in zip(weights, bounds, strict=True)) for j in (0, 1)
            ]
            lo, hi = ref.envelope(low, high, case["cap"], case["hidden_cap"])
            components = [
                SCORE_SPAN * w * (b[1] - b[0]) for w, b in zip(weights, bounds, strict=True)
            ]
            expansion = SCORE_SPAN * case["cap"] * (low + max(case["hidden_cap"] - high, 0))
            truth = ref.score(
                (1 - case["mass"])
                * math.fsum(w * p for w, p in zip(weights, case["rates"], strict=True))
                + case["mass"] * case["hidden"]
            )
            left, right = ref.score(lo), ref.score(hi)
            width = right - left
            covered = left <= truth <= right
            precise = width <= cfg["target_width"]
            ref.require(ref.same(width, math.fsum([*components, expansion])), "width decomposition")
            ref.require(ref.same(width, float(row["width"])), "published raw width")
            ref.require(int(row["coverage"]) == covered, "coverage classification")
            ref.require(int(row["useful"]) == (covered and precise), "useful classification")
            idx = int(row["replicate"])
            ref.require(idx not in groups[method], "duplicate primary row")
            groups[method][idx] = (width, *components, expansion, covered, precise)
    result = {}
    n = data["tokens"]["n"]
    for method in methods:
        records = groups[method]
        ref.require(set(records) == set(range(n)), (method, "primary inventory"))
        fields = ("width", "low_stratum_width", "high_stratum_width", "envelope_increment")
        values = {
            f"mean_{field}": mean(r[i] for r in records.values()) for i, field in enumerate(fields)
        }
        for k, value in values.items():
            ref.require(ref.same(value, data["diagnostics"][method][k]), (method, k))
        useful = sum(r[4] and r[5] for r in records.values())
        ref.require(useful == data["allocation"][method]["useful"]["count"], "useful count")
        result[method] = {
            **values,
            "n": n,
            "covered": sum(r[4] for r in records.values()),
            "precise": sum(r[5] for r in records.values()),
            "covered_and_precise": useful,
        }
    return result


def compare_large_omission():
    rows = json.loads((EXTENSION / "results.json").read_text())["summary"]
    found = {
        row["method"]: row
        for row in rows
        if (row["case"], row["budget"]) == ("large_omission", 32768)
        and row["method"] in {"reachable_only", "equal_envelope"}
    }
    direct, envelope = (found[k] for k in ("reachable_only", "equal_envelope"))
    for key in ("independent_units", "charged_rows", "acquisition_cost"):
        ref.require(direct[key] == envelope[key], ("Phase 19", key))
    return {
        "n": envelope["rates"]["coverage"]["n"],
        "reachable_only_covered": direct["rates"]["coverage"]["count"],
        "equal_envelope_covered": envelope["rates"]["coverage"]["count"],
        "equal_envelope_covered_and_precise": envelope["rates"]["coverage_with_precision"]["count"],
        "matched_charged_units": envelope["acquisition_cost"],
    }


def render_final(output, figures, data, receipt):
    source_path = DOC / "MANUSCRIPT.md"
    bibliography = DOC / "REFERENCES.md"
    source = publication.substitute(source_path.read_text(), data["tokens"])
    references = bibliography.read_text()
    cited = dict.fromkeys(
        int(n) for group in re.findall(r"\[([0-9, ]+)\]", source) for n in group.split(",")
    )
    listed = [int(n) for n in re.findall(r"^\[([0-9]+)\] ", references, re.MULTILINE)]
    ref.require(list(cited) == listed == list(range(1, 13)), "citation inventory and order")
    output.mkdir()
    (output / "figures").symlink_to(figures.resolve())
    try:
        publication.render(output, source + "\n\n" + references, publication.tables(data))
    finally:
        (output / "figures").unlink()
    updated = {
        **receipt,
        "source_sha256": {
            str(p.relative_to(ROOT)): ref.sha(p)
            for p in (source_path, bibliography, Path(__file__))
        },
        "pdf_sha256": ref.sha(output / "GENEVRA-manuscript.pdf"),
        "rendered_evidence_tokens": data["tokens"],
    }
    publication.write_json(output / "audit-receipt.json", dict(sorted(updated.items())))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("replay", type=Path, nargs="?", help="completed Phase 28 reproduction")
    parser.add_argument("output", type=Path, help="new final audit directory")
    args = parser.parse_args()
    data = publication.evidence()
    large = compare_large_omission()
    data["tokens"]["large_direct_cover"] = large["reachable_only_covered"]
    expected = ROOT / "docs/research/phase_27/reference-verification.json"
    expected_raw = json.loads(expected.read_text())["phase25_raw_sha256"]
    if args.replay is None:
        # Publication-only path. Reuse the audited counts and frozen figure bytes.
        receipt = json.loads((DOC / "rendered/audit-receipt.json").read_text())
        ref.require(receipt["reference_sha256"] == ref.sha(expected), "frozen reference receipt")
        ref.require(receipt["phase25_raw_sha256"] == expected_raw, "frozen raw digest")
        ref.require(receipt["rendered_evidence_tokens"] == data["tokens"], "frozen numeric text")
        ref.require(receipt["matched_large_omission"] == large, "frozen omission comparison")
        figures = PHASE28 / "rendered/figures"
    else:
        reference = args.replay / "reference-verification.json"
        raw = args.replay / "phase25/raw.csv"
        ref.require(ref.sha(reference) == ref.sha(expected), "Phase 27 reference reproduction")
        ref.require(ref.sha(raw) == expected_raw, "Phase 25 raw evidence digest")
        receipt = {
            "schema": "genevra-final-audit-v1",
            "status": "passed",
            "reference_sha256": ref.sha(reference),
            "phase25_raw_sha256": ref.sha(raw),
            "primary_width_reconstruction": check_width_records(raw, data),
            "matched_large_omission": large,
            "external_reproduction": "outstanding",
            "empirical_validation": "outstanding",
        }
        figures = args.replay / "manuscript/figures"
    render_final(args.output, figures, data, receipt)


if __name__ == "__main__":
    main()
