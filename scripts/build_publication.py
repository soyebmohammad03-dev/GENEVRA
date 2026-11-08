"""Build the GENEVRA Phase 28 manuscript and figures from frozen evidence."""

import argparse
import csv
import hashlib
import json
import math
import re
from pathlib import Path
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / "docs/research/phase_28"
RESEARCH = ROOT / "docs/research"
EXTENSION = ROOT / "docs/model_repair/phase_19/extension"
METHODS = ("width_proxy", "variance", "equal_spend")
LABELS = ("Width proxy", "Pilot Neyman", "Equal spend")
COLORS = ("#9C402C", "#177A78", "#385D9D")
SENSITIVITY = {
    "reference": "Reference",
    "pilot_32": "Pilot 32 per stratum",
    "pilot_512": "Pilot 512 per stratum",
    "equal_tariffs": "Equal tariffs",
    "large_omission": "Large omission",
    "strict_width": "Width limit 0.50",
    "loose_width": "Width limit 0.75",
    "budget_65536": "Budget 65,536",
}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + "\n")


def evidence():
    paths = {
        "reference": RESEARCH / "phase_27/reference-verification.json",
        "allocation": RESEARCH / "phase_25/results.json",
        "diagnostics": RESEARCH / "phase_26/reconstruction.json",
        "sensitivity": RESEARCH / "phase_26/sensitivity.json",
        "extension": EXTENSION / "results.json",
        "extension_config": EXTENSION / "config.json",
    }
    data = {key: json.loads(path.read_text()) for key, path in paths.items()}
    reference = data["reference"]
    if reference["status"] != "passed":
        raise ValueError("reference did not pass")
    phase18 = reference["phase18"]
    primary = next(row for row in reference["phase25"]["contrasts"] if row["primary"])
    public_primary = next(row for row in data["allocation"]["contrasts"] if row["primary"])
    if [primary["difference"], *primary["interval"]] != [
        public_primary[k] for k in ("difference", "low", "high")
    ]:
        raise ValueError("primary contrast mismatch")
    case, budget, n = (primary[k] for k in ("case", "budget", "n"))
    allocation = [
        next(
            r
            for r in data["allocation"]["summary"]
            if (r["case"], r["budget"], r["method"]) == (case, budget, method)
        )
        for method in METHODS
    ]
    for method, row in zip(METHODS, allocation, strict=True):
        ref = next(
            r
            for r in reference["phase25"]["cells"]
            if (r["case"], r["budget"], r["method"]) == (case, budget, method)
        )
        if any(ref[k] != row[k]["count"] for k in ("coverage", "useful", "false_certificate")):
            raise ValueError("allocation counts mismatch")
    large = next(
        r
        for r in data["extension"]["summary"]
        if (r["case"], r["budget"], r["method"]) == ("large_omission", budget, "equal_envelope")
    )
    cap = next(r["cap"] for r in data["extension_config"]["cases"] if r["name"] == "large_omission")
    shared = phase18["shared_blind"]
    # The denominator is frozen in Phase 18's design. Cross-check it via the exact bound.
    shared_n = 512
    upper = phase18["simultaneous_false_certificate_upper"]["shared_blind"]
    k = shared["false_certificate"]
    tail = sum(
        math.comb(shared_n, i) * upper**i * (1 - upper) ** (shared_n - i) for i in range(k + 1)
    )
    if not math.isclose(tail, 0.05 / 9, abs_tol=1e-12):
        raise ValueError("shared-blind risk denominator mismatch")
    tokens = {
        "shared_n": shared_n,
        "shared_cover": shared["coverage"],
        "shared_issued": shared["certificate"],
        "shared_false": shared["false_certificate"],
        "shared_wrong_label": shared["wrong_call"],
        "shared_upper": f"{100 * upper:.2f}",
        "n": n,
        "budget": f"{budget:,}",
        "proxy": allocation[0]["useful"]["count"],
        "neyman": allocation[1]["useful"]["count"],
        "equal": allocation[2]["useful"]["count"],
        "difference": f"{100 * primary['difference']:.2f}",
        "low": f"{100 * primary['interval'][0]:.2f}",
        "high": f"{100 * primary['interval'][1]:.2f}",
        "discordant": primary["variance_only"],
        "secondary": sum(
            not r["primary"] and r["interval"][0] <= 0 <= r["interval"][1]
            for r in reference["phase25"]["contrasts"]
        ),
        "large_n": large["rates"]["coverage"]["n"],
        "large_cover": large["rates"]["coverage"]["count"],
        "large_useful": large["rates"]["coverage_with_precision"]["count"],
        "large_floor": f"{234.2 * cap:.3f}",
        "cells": len(reference["phase25"]["cells"]),
        "records": f"{reference['phase25']['replicate_records']:,}",
    }
    diag = data["diagnostics"]["primary_diagnostics"]
    for label, method in zip(("proxy", "neyman", "equal"), METHODS, strict=True):
        for key in ("n1", "low_stratum_width", "high_stratum_width", "envelope_increment", "width"):
            tokens[f"{label}_{key}"] = f"{diag[method][f'mean_{key}']:.4f}"
    return {
        "source_sha256": {str(p.relative_to(ROOT)): sha(p) for p in paths.values()},
        "tokens": tokens,
        "allocation": dict(zip(METHODS, allocation, strict=True)),
        "diagnostics": {m: diag[m] for m in METHODS},
        "sensitivity_exploratory": {
            name: {m: data["sensitivity"][name][m] for m in METHODS} for name in SENSITIVITY
        },
    }


def tables(data):
    v = data["tokens"]
    notation = [
        ("Symbol", "Meaning"),
        ("T, F_A, F_B", "Target population and two sampling frames"),
        ("w_h, p_h", "Reachable stratum weight and Bernoulli tail rate"),
        ("r, m, z", "Reachable mixture rate, omitted mass, hidden tail rate"),
        ("U, V", "Externally supplied upper bounds on omitted mass and hidden tail rate"),
        ("c_h, n_h, B", "Unit price, independent-unit count, charged acquisition budget"),
        ("a, δ, ε, τ", "Anchor score, certificate tolerance, decision threshold, width limit"),
        ("I=[L,H], θ", "Score interval and target score mean"),
    ]
    shared = [
        ("Endpoint", "Count", "Denominator"),
        ("Mean coverage", v["shared_cover"], v["shared_n"]),
        ("Certificates issued", v["shared_issued"], v["shared_n"]),
        ("False certificates (all runs)", v["shared_false"], v["shared_n"]),
        ("False certificates (among issued)", v["shared_false"], v["shared_issued"]),
        ("Wrong threshold labels", v["shared_wrong_label"], v["shared_n"]),
    ]
    allocation = [
        ("Allocation", "Covered", "Covered and precise", "Mean width (score units)"),
        *[
            (
                label,
                f"{data['allocation'][m]['coverage']['count']}/{v['n']}",
                f"{data['allocation'][m]['useful']['count']}/{v['n']}",
                f"{data['diagnostics'][m]['mean_width']:.4f}",
            )
            for label, m in zip(LABELS, METHODS, strict=True)
        ],
    ]
    sensitivity = [
        ("Exploratory setting", *LABELS),
        *[
            (label, *(f"{rs[m]['useful']}/{rs[m]['n']}" for m in METHODS))
            for name, label in SENSITIVITY.items()
            for rs in [data["sensitivity_exploratory"][name]]
        ],
    ]
    return {
        "notation": notation,
        "shared": shared,
        "allocation": allocation,
        "sensitivity": sensitivity,
    }


def figures(output, data):
    import matplotlib

    matplotlib.use("Agg")
    from matplotlib import pyplot as plt

    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10})
    v = data["tokens"]

    def save(fig, name):
        fig.savefig(output / f"{name}.png", dpi=270, facecolor="white")
        plt.close(fig)

    def diagram(title, rows, name):
        fig, ax = plt.subplots(figsize=(8, 2.3), layout="constrained")
        ax.set(xlim=(0, 1), ylim=(0, 1))
        ax.axis("off")
        ax.set_title(title, loc="left", weight="bold", pad=10)
        xs = (0.17, 0.50, 0.83)
        for row, y in zip(rows, (0.70, 0.26), strict=True):
            for j, (x, content) in enumerate(zip(xs, row, strict=True)):
                ax.text(
                    x,
                    y,
                    content,
                    ha="center",
                    va="center",
                    fontsize=9.5,
                    bbox={"boxstyle": "round,pad=.52", "fc": "#EAF1F5", "ec": "#7B94A5"},
                )
                if j < 2:
                    ax.annotate(
                        "",
                        xy=(x + 0.245, y),
                        xytext=(x + 0.11, y),
                        arrowprops={"arrowstyle": "->", "color": "#607886"},
                    )
        save(fig, name)

    diagram(
        "Benchmark and reproduction architecture",
        [
            (
                "Target law +\nframe restrictions",
                "Common paid pilot +\nmatched tariff",
                "Paired inference\nand decisions",
            ),
            (
                "Frozen configuration\nand raw hashes",
                "Separate reference\nreconstruction",
                "Verified tables,\nfigures and report",
            ),
        ],
        "design",
    )
    diagram(
        "Decision diagnostic",
        [
            (
                "Target and access\nassumptions",
                "Mean interval\ncoverage + width",
                "Threshold call\nor abstention",
            ),
            (
                "Anchor tolerance\nand interval",
                "Issue or withhold\ncertificate",
                "False / all runs\nFalse / issued",
            ),
        ],
        "diagnostic",
    )

    fig, axes = plt.subplots(1, 2, figsize=(8, 2.65), layout="constrained")
    for ax, pairs, title in [
        (
            axes[0],
            [
                ("Mean coverage", v["shared_cover"], v["shared_n"]),
                ("False certificates", v["shared_false"], v["shared_n"]),
            ],
            "All runs",
        ),
        (axes[1], [("False among issued", v["shared_false"], v["shared_issued"])], "Issued only"),
    ]:
        for j, (_, k, n) in enumerate(pairs):
            ax.barh(j, 100 * k / n, color=COLORS[j], height=0.42)
            ax.text(min(100 * k / n + 3, 101), j, f"{k}/{n}", va="center")
        ax.set(
            yticks=range(len(pairs)),
            yticklabels=[p[0] for p in pairs],
            xlim=(0, 122),
            xticks=(0, 25, 50, 75, 100),
            title=title,
            xlabel="Percent of denominator",
        )
        ax.invert_yaxis()
    fig.suptitle("Shared blindness separates coverage from certificate safety", weight="bold")
    save(fig, "shared")

    fig, axes = plt.subplots(1, 2, figsize=(8, 3.05), layout="constrained")
    for i, method in enumerate(METHODS):
        row = data["allocation"][method]
        axes[0].barh(
            i - 0.15,
            100 * row["coverage"]["rate"],
            height=0.24,
            color="#CDD9E3",
            label="Covered" if i == 0 else None,
        )
        axes[0].barh(i + 0.15, 100 * row["useful"]["rate"], height=0.24, color=COLORS[i])
        axes[0].text(
            100 * row["useful"]["rate"] + 2,
            i + 0.15,
            str(row["useful"]["count"]),
            va="center",
            fontsize=9,
        )
        diag = data["diagnostics"][method]
        left = 0
        for j, key in enumerate(("low_stratum_width", "high_stratum_width", "envelope_increment")):
            width = diag[f"mean_{key}"]
            axes[1].barh(
                i,
                width,
                left=left,
                color=("#849CB2", "#35577B", "#CE9550")[j],
                label=("Low stratum", "High stratum", "Envelope")[j] if i == 0 else None,
            )
            left += width
    for ax in axes:
        ax.set_yticks(range(3), LABELS)
        ax.invert_yaxis()
    axes[0].set(xlim=(0, 114), xlabel="Percent of runs", title="Coverage and useful precision")
    axes[0].text(
        0.01,
        -0.28,
        "Colored bars: covered and precise. Labels: counts.",
        transform=axes[0].transAxes,
        fontsize=8,
    )
    axes[1].axvline(0.60, color="#222222", linestyle=":", lw=1.3)
    axes[1].set(xlim=(0, 0.75), xlabel="Mean width (score units)", title="Width decomposition")
    axes[1].legend(
        loc="upper center", bbox_to_anchor=(0.5, -0.24), ncol=3, fontsize=7, frameon=False
    )
    fig.suptitle(f"Matched allocation at {v['budget']} charged units", weight="bold")
    save(fig, "allocation")

    fig, ax = plt.subplots(figsize=(7.5, 3.25), layout="constrained")
    raw = [[data["sensitivity_exploratory"][k][m] for m in METHODS] for k in SENSITIVITY]
    fractions = [[row["useful"] / row["n"] for row in group] for group in raw]
    img = ax.imshow(fractions, vmin=0, vmax=1, cmap="Blues", aspect="auto")
    for i, group in enumerate(raw):
        for j, row in enumerate(group):
            ax.text(
                j,
                i,
                f"{row['useful']}/{row['n']}",
                ha="center",
                va="center",
                color="white" if fractions[i][j] > 0.55 else "#142A41",
                fontsize=9,
            )
    ax.set(
        xticks=range(3),
        xticklabels=LABELS,
        yticks=range(len(SENSITIVITY)),
        yticklabels=list(SENSITIVITY.values()),
        title="Exploratory useful precision sensitivity",
    )
    fig.colorbar(img, ax=ax, label="Fraction covered and precise")
    save(fig, "sensitivity")


def substitute(source, tokens):
    pattern = r"\{\{([a-z0-9_]+)\}\}"
    expanded = re.sub(pattern, lambda match: str(tokens[match[1]]), source)
    if "{{" in expanded or "}}" in expanded:
        raise ValueError("unresolved manuscript placeholder")
    return expanded


def render(output, source, table_data):
    import matplotlib
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_LEFT
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.pdfgen import canvas
    from reportlab.platypus import (
        Image,
        KeepTogether,
        Paragraph,
        SimpleDocTemplate,
        Spacer,
        Table,
        TableStyle,
    )

    fonts = Path(matplotlib.get_data_path()) / "fonts/ttf"
    for style, name in (
        ("Paper", "DejaVuSerif.ttf"),
        ("PaperBold", "DejaVuSerif-Bold.ttf"),
        ("PaperSans", "DejaVuSans.ttf"),
    ):
        pdfmetrics.registerFont(TTFont(style, str(fonts / name)))
    styles = getSampleStyleSheet()
    for key, font, size, leading, before, after in (
        ("Body", "Paper", 9.9, 14.3, 0, 7),
        ("TitleText", "PaperBold", 22, 27, 0, 14),
        ("Section", "PaperBold", 14, 18, 12, 5),
        ("Subsection", "PaperBold", 11, 14, 8, 4),
        ("Reference", "Paper", 9.1, 12.1, 0, 5),
        ("Caption", "PaperSans", 8.2, 11.1, 4, 9),
        ("Cell", "PaperSans", 8.1, 10.8, 0, 0),
    ):
        styles.add(
            ParagraphStyle(
                name=key,
                fontName=font,
                fontSize=size,
                leading=leading,
                spaceBefore=before,
                spaceAfter=after,
                alignment=TA_LEFT,
                keepWithNext=key in {"TitleText", "Section", "Subsection"},
                textColor=colors.HexColor("#172637"),
            )
        )

    def paragraph(s, style="Body"):
        escaped = escape(s)
        linked = re.sub(
            r"\[([^\]]+)\]\((https?://[^)]+)\)",
            r'<link href="\2" color="#235B86">\1</link>',
            escaped,
        )
        return Paragraph(linked, styles[style])

    doc = SimpleDocTemplate(
        str(output / "GENEVRA-manuscript.pdf"),
        pagesize=letter,
        rightMargin=58,
        leftMargin=58,
        topMargin=54,
        bottomMargin=48,
        title="GENEVRA: Certification under shared sampling-frame undercoverage",
        author="Soyeb Mohammad",
    )
    story = []
    for block in source.strip().split("\n\n"):
        line = block.strip()
        if line.startswith("@"):
            directive, name, caption = line.split(" ", 2)
            if directive == "@figure":
                item = Image(str(output / "figures" / f"{name}.png"))
                item.drawHeight *= doc.width / item.drawWidth
                item.drawWidth = doc.width
            elif directive == "@table":
                rows = [[paragraph(str(cell), "Cell") for cell in row] for row in table_data[name]]
                width = doc.width
                columns = (
                    [width * 0.37, width * 0.63]
                    if len(rows[0]) == 2
                    else [width * 0.40, *([width * 0.60 / (len(rows[0]) - 1)] * (len(rows[0]) - 1))]
                )
                item = Table(rows, colWidths=columns, repeatRows=1)
                item.setStyle(
                    TableStyle(
                        [
                            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#DFEAF1")),
                            (
                                "ROWBACKGROUNDS",
                                (0, 1),
                                (-1, -1),
                                [colors.white, colors.HexColor("#F4F7FA")],
                            ),
                            ("VALIGN", (0, 0), (-1, -1), "TOP"),
                            ("TOPPADDING", (0, 0), (-1, -1), 4),
                            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                        ]
                    )
                )
            else:
                raise ValueError(directive)
            story.append(KeepTogether([Spacer(1, 5), item, paragraph(caption, "Caption")]))
            continue
        if line.startswith("#"):
            prefix, title = line.split(" ", 1)
            story.append(
                paragraph(title, {"#": "TitleText", "##": "Section", "###": "Subsection"}[prefix])
            )
        else:
            style = "Reference" if re.match(r"^\[\d+\]", line) else "Body"
            story.append(paragraph(" ".join(line.splitlines()), style))

    def footer(page, document):
        page.setStrokeColor(colors.HexColor("#C2D0DA"))
        page.line(58, 39, 554, 39)
        page.setFont("PaperSans", 8)
        page.setFillColor(colors.HexColor("#51667A"))
        page.drawString(58, 26, "GENEVRA  |  Manuscript prepared for independent review")
        page.drawRightString(554, 26, str(document.page))

    def deterministic_canvas(*args, **kwargs):
        kwargs["invariant"] = 1
        return canvas.Canvas(*args, **kwargs)

    doc.build(story, onFirstPage=footer, onLaterPages=footer, canvasmaker=deterministic_canvas)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    output = args.output
    output.mkdir()
    (output / "figures").mkdir()
    (output / "tables").mkdir()
    data = evidence()
    write_json(output / "evidence.json", data)
    table_data = tables(data)
    for key, values in table_data.items():
        with (output / "tables" / f"{key}.csv").open("x", encoding="utf-8", newline="") as stream:
            csv.writer(stream, lineterminator="\n").writerows(values)
    figures(output / "figures", data)
    source = substitute((DOC / "MANUSCRIPT.md").read_text(), data["tokens"])
    references = (DOC / "REFERENCES.md").read_text()
    render(output, source + "\n\n" + references, table_data)
    paths = [
        DOC / "MANUSCRIPT.md",
        DOC / "REFERENCES.md",
        DOC / "requirements-publication.txt",
        RESEARCH / "phase_23/requirements-macos-arm64.txt",
        Path(__file__).resolve(),
    ]
    write_json(
        output / "build-receipt.json",
        {
            "source_sha256": {str(p.relative_to(ROOT)): sha(p) for p in paths},
            "outputs_sha256": {
                str(p.relative_to(output)): sha(p) for p in sorted(output.rglob("*")) if p.is_file()
            },
        },
    )


if __name__ == "__main__":
    main()
