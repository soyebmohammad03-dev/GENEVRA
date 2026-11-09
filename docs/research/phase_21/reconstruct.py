"""Reconstruct the Phase 21 Census reference sensitivity and national net error."""

import argparse
import hashlib
import html
import json
import re
from decimal import Decimal
from pathlib import Path
from xml.etree import ElementTree
from zipfile import ZipFile

NS = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"


def workbook_values(path: Path) -> dict[str, str]:
    """Read the pinned workbook's first sheet without executing formulas."""
    with ZipFile(path) as z:
        shared = ElementTree.fromstring(z.read("xl/sharedStrings.xml"))
        strings = ["".join(t.text or "" for t in node.iter(NS + "t")) for node in shared]
        workbook = ElementTree.fromstring(z.read("xl/workbook.xml"))
        sheet = next(workbook.iter(NS + "sheet"))
        if sheet.attrib["name"] != "Table 3":
            raise ValueError("unexpected sheet")
        document = ElementTree.fromstring(z.read("xl/worksheets/sheet1.xml"))
    cells = {}
    for cell in document.iter(NS + "c"):
        value = cell.findtext(NS + "v")
        if value is not None:
            cells[cell.attrib["r"]] = strings[int(value)] if cell.get("t") == "s" else value
    return cells


def release_row(source: str) -> list[str]:
    matched = []
    for row in re.findall(r"<tr\b[^>]*>(.*?)</tr>", source, re.IGNORECASE | re.DOTALL):
        fields = [
            html.unescape(re.sub(r"<[^>]+>", "", value)).strip()
            for value in re.findall(r"<td\b[^>]*>(.*?)</td>", row, re.IGNORECASE | re.DOTALL)
        ]
        if len(fields) == 4 and fields[0] == "United States":
            matched.append(fields)
    if len(matched) != 1:
        raise ValueError("expected one national release row")
    return matched[0]


def analyze(workbook: Path, release: Path, provenance: dict) -> dict:
    digest = hashlib.sha256(workbook.read_bytes()).hexdigest()
    if digest != provenance["march_2022_workbook"]["sha256"]:
        raise ValueError("workbook hash mismatch")
    cells = workbook_values(workbook)
    labels = [cells[f"{column}3"] for column in "CDE"]
    if labels != ["Low", "Middle", "High"] or (cells["A4"], cells["A5"]) != ("Total", "0-4"):
        raise ValueError("unexpected series or population")
    rates = [Decimal(cells[f"{column}5"]) for column in "CDE"]
    row = release_row(release.read_text())
    if row != provenance["april_2024_release"]["row"]:
        raise ValueError("published national values changed")
    da, count = (int(s.replace(",", "")) for s in row[1:3])
    rate = 100 * Decimal(count - da) / da
    if rate.quantize(Decimal(".01")) != Decimal(row[3]):
        raise ValueError("national count reconstruction does not match published rounding")
    return {
        "population": "U.S. ages 0–4, both sexes",
        "march_2022_net_error_percent": dict(zip(labels, map(float, rates), strict=True)),
        "march_2022_series_span_percentage_points": float(max(rates) - min(rates)),
        "april_2024": {
            "census_count": count,
            "da_estimate": da,
            "count_minus_estimate": count - da,
            "net_error_percent": float(rate),
            "published_percent": float(row[3]),
        },
    }


def plot(result: dict, path: Path) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    figure, ax = plt.subplots(figsize=(6.5, 3.1), layout="constrained")
    rates = result["march_2022_net_error_percent"]
    labels = [f"2022 {key.lower()} series" for key in rates] + ["2024 national tabulation"]
    values = list(rates.values()) + [result["april_2024"]["net_error_percent"]]
    ax.barh(labels, values, color=["#267583"] * 3 + ["#68788f"], height=0.57)
    for i, value in enumerate(values):
        ax.text(value + 0.1, i, f"{value:.2f}%", color="white", va="center")
    ax.axhline(2.5, color="#96a2b0", linewidth=0.8)
    ax.invert_yaxis()
    ax.set(
        xlim=(-6, 0),
        xlabel="Published-vintage net coverage error (%)",
        title="2020 U.S. Census coverage, ages 0–4",
    )
    ax.spines[["top", "right"]].set_visible(False)
    figure.savefig(path, dpi=180)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("workbook", type=Path)
    parser.add_argument("release_html", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--figure", type=Path)
    args = parser.parse_args()
    provenance = json.loads(Path(__file__).with_name("provenance.json").read_text())
    result = analyze(args.workbook, args.release_html, provenance)
    with args.output.open("x") as stream:
        json.dump(result, stream, indent=2, ensure_ascii=False)
        stream.write("\n")
    if args.figure:
        plot(result, args.figure)


if __name__ == "__main__":
    main()
