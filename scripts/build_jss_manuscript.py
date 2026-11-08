"""Convert frozen Phase 29 manuscript and table values to the JSS draft."""

import argparse
import csv
import json
import re
import textwrap
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PHASE = ROOT / "docs/research/phase_29"
DRAFT = PHASE / "jss"
TABLES = PHASE.parent / "phase_28/rendered/tables"
KEYS = (
    "manski2005",
    "imbens2004",
    "tudball2023",
    "lohr2006",
    "volstad2020",
    "geifman2017",
    "angelopoulos2025",
    "neyman1934",
    "wright2019",
    "morris2019",
    "hoeffding1963",
    "clopper1934",
)
MATH = {
    "T outside F_A union F_B": r"T\setminus(F_A\cup F_B)",
    "r = \u03a3_h w_h p_h": r"r=\sum_h w_h p_h",
    "q_T = (1\u2212m)r + mz": r"q_T=(1-m)r+mz",
    "\u03b8 = 0.30 + 234.2 q_T": r"\theta=0.30+234.2q_T",
    "[(1\u2212U)l, u + U max(V\u2212u,0)]": r"[(1-U)l,u+U\max(V-u,0)]",
    "239.45 max(|p_L\u2212p_S|,|p_U\u2212p_S|) + 239.55 q_U \u2264 \u03b4": (
        r"239.45\max(|p_L-p_S|,|p_U-p_S|)+239.55q_U\leq\delta"
    ),
    "\u03a3_h w_h / sqrt(n_h)": r"\sum_h w_h\allowbreak/\sqrt{n_h}",
    "\u03a3_h w_h\u00b2 v_h / n_h": r"\sum_h w_h^2 v_h\allowbreak/n_h",
    "sqrt(2 log(2/\u03b1)/n)": r"\sqrt{2\log(2/\alpha)/n}",
    "234.2 \u03a3_h w_h (u_h\u2212l_h)": r"234.2\sum_h w_h(u_h-l_h)",
    "log(\u03b1/4)": r"\log(\alpha/4)",
    "0 \u2264 m \u2264 U": r"0\leq m\leq U",
    "0 \u2264 z \u2264 V": r"0\leq z\leq V",
    "L \u2264 \u03b8 \u2264 H": r"L\leq\theta\leq H",
    "H\u2212L \u2264 \u03c4": r"H-L\leq\tau",
    "L > \u03b5": r"L>\epsilon",
    "H \u2264 \u03b5": r"H\leq\epsilon",
    "[a\u2212\u03b4,a+\u03b4]": r"[a-\delta,a+\delta]",
    "|\u03b8\u2212a| > \u03b4": r"|\theta-a|>\delta",
    "k_h/n_h": "k_h/n_h",
    "234.2 U": "234.2U",
    "V=1": "V=1",
    "\u03b1=.05/3": r"\alpha=.05/3",
    "\u03b1=.05/17": r"\alpha=.05/17",
    "\u03b1=.05": r"\alpha=.05",
    "[\u22122,2]": "[-2,2]",
    "[\u22121,1]": "[-1,1]",
}
MATH.update(
    {
        s: s
        for s in (
            "F_A",
            "F_B",
            "w_h",
            "p_h",
            "q_T",
            "k_h",
            "n_h",
            "p_S",
            "p_L",
            "p_U",
            "q_U",
            "v_h",
            "c_h",
            "D_j",
            "[l,u]",
            "[L,H]",
            "I=[L,H]",
        )
    }
)
ESCAPES = {
    "%": r"\%",
    "&": r"\&",
    "#": r"\#",
    "_": r"\_",
    "\u2212": "-",
    "\u2013": "--",
    "\u2019": "'",
    "\u201c": chr(96) * 2,
    "\u201d": "''",
    "\u03b4": r"\ensuremath{\delta}",
    "\u03b5": r"\ensuremath{\epsilon}",
    "\u03c4": r"\ensuremath{\tau}",
    "\u03b8": r"\ensuremath{\theta}",
}
TOKEN = re.compile(
    "|".join(
        [
            r"\[[0-9]+(?:,[0-9]+)*\]",
            *[re.escape(x) for x in sorted(MATH, key=len, reverse=True)],
            *map(re.escape, ESCAPES),
        ]
    )
)


def latex(text):
    """Escape prose and typeset the manuscript's explicit math and citations."""

    def replace(match):
        token = match[0]
        if token in MATH:
            return r"\(" + MATH[token] + r"\)"
        if token in ESCAPES:
            return ESCAPES[token]
        return r"\citep{" + ",".join(KEYS[int(i) - 1] for i in token[1:-1].split(",")) + "}"

    return TOKEN.sub(replace, text)


def table(name, caption):
    with (TABLES / f"{name}.csv").open(newline="", encoding="utf-8") as f:
        rows = list(csv.reader(f))
    align = {
        "notation": r"lp{0.64\linewidth}",
        "shared": "lrr",
        "allocation": r"lrrp{0.19\linewidth}",
        "sensitivity": "lrrr",
    }[name]
    body = [" & ".join(map(latex, row)) + r" \\" for row in rows]
    return "\n".join(
        [
            r"\begin{table}[htbp]",
            r"\centering",
            r"\small",
            r"\begin{tabular}{" + align + "}",
            r"\hline",
            body[0],
            r"\hline",
            *body[1:],
            r"\hline",
            r"\end{tabular}",
            r"\caption{" + latex(caption) + "}",
            r"\label{tab:" + name + "}",
            r"\end{table}",
        ]
    )


def build():
    frozen = (PHASE / "MANUSCRIPT.md").read_text()
    values = json.loads((PHASE / "rendered/audit-receipt.json").read_text())[
        "rendered_evidence_tokens"
    ]
    source = re.sub(r"\{\{([a-z_0-9]+)\}\}", lambda m: str(values[m[1]]), frozen)
    title, _, abstract_heading, abstract, keywords, *body = source.strip().split("\n\n")
    if abstract_heading != "## Abstract" or not keywords.startswith("Keywords: "):
        raise ValueError("unexpected manuscript front matter")
    urls = re.findall(r"\]\((https://[^)]+)\)", (PHASE / "REFERENCES.md").read_text())
    bib = (DRAFT / "references.bib").read_text(encoding="ascii")
    expected = [
        "https://doi.org/" + v if field == "doi" else v
        for field, v in re.findall(r"\b(doi|url)\s*=\s*\{([^}]+)\}", bib)
    ]
    cited = dict.fromkeys(
        int(i) for group in re.findall(r"\[([0-9,]+)\]", source) for i in group.split(",")
    )
    if urls != expected or list(cited) != list(range(1, len(KEYS) + 1)):
        raise ValueError("bibliography or citation order differs from frozen manuscript")
    if tuple(re.findall(r"^@\w+\{([^,]+),", bib, re.M)) != KEYS:
        raise ValueError("BibTeX keys differ from manuscript citation mapping")
    output = [
        "% Generated by scripts/build_jss_manuscript.py from Phase 29.",
        r"\documentclass[article,nojss]{jss}",
        r"\usepackage{lmodern}",
        r"\setlength{\emergencystretch}{2em}",
        r"\author{Soyeb Mohammad}",
        r"\Plainauthor{Soyeb Mohammad}",
        r"\Address{Soyeb Mohammad\\Author affiliation and correspondence pending confirmation.}",
        r"\title{When Sampling Frames Share a Blind Spot: A Reproducible Benchmark for "
        r"Population-Mean Certification}",
        r"\Plaintitle{" + title[2:] + "}",
        r"\Shorttitle{Certification under Shared Undercoverage}",
        r"\Abstract{" + latex(abstract) + "}",
        r"\Keywords{" + keywords.removeprefix("Keywords: ") + "}",
        r"\Plainkeywords{" + keywords.removeprefix("Keywords: ") + "}",
        r"\begin{document}",
    ]
    inventory = []
    for block in body:
        if block.startswith("### "):
            output.append(r"\subsection{" + latex(block[4:]) + "}")
        elif block.startswith("## "):
            if block == "## 9. Conclusion":
                output.append(r"""\subsection{Software and worked reproduction}
The \pkg{GENEVRA} research drivers are written in \proglang{Python}. The archival
runner verifies the capsule before replay. The independent reference reads
stored counts and independently verifies intervals and decisions. The publication
driver reads checked evidence and renders the manuscript assets. The software
guide documents the module interfaces, installation, and error handling.

From the repository root the following command rebuilds the Phase 29 review PDF
from frozen artifacts. It checks the output against the published bytes.
\begin{Code}
sh scripts/reproduce_final_research.sh --publication-only /tmp/genevra-review
\end{Code}
The software guide also gives the separate complete historical replay command.
Figures~\ref{fig:diagnostic} and~\ref{fig:design} describe the workflow.
Figures~\ref{fig:shared}, \ref{fig:allocation}, and~\ref{fig:sensitivity}
and Tables~\ref{tab:notation}, \ref{tab:shared}, \ref{tab:allocation},
and~\ref{tab:sensitivity} are produced from the existing publication inputs.""")
            output.append(r"\section{" + latex(re.sub(r"^## [0-9]+\. ", "", block)) + "}")
        elif block.startswith("@"):
            kind, name, label, _, caption = block.split(" ", 4)
            inventory.append((kind, name))
            if kind == "@figure" and label == "Figure":
                output.append(
                    "\n".join(
                        [
                            r"\begin{figure}[htbp]",
                            r"\centering",
                            r"\includegraphics[width=\linewidth]{figures/" + name + ".png}",
                            r"\caption{" + latex(caption) + "}",
                            r"\label{fig:" + name + "}",
                            r"\end{figure}",
                        ]
                    )
                )
            elif kind == "@table" and label == "Table":
                output.append(table(name, caption))
            else:
                raise ValueError("unexpected figure or table directive")
        else:
            output.append(
                textwrap.fill(
                    latex(block), width=72, break_long_words=False, break_on_hyphens=False
                )
            )
    if inventory != [
        ("@table", "notation"),
        ("@figure", "diagnostic"),
        ("@figure", "design"),
        ("@figure", "shared"),
        ("@table", "shared"),
        ("@table", "allocation"),
        ("@figure", "allocation"),
        ("@figure", "sensitivity"),
        ("@table", "sensitivity"),
    ]:
        raise ValueError("frozen figure or table inventory changed")
    output.extend([r"\bibliography{references}", r"\end{document}"])
    return "\n\n".join(output) + "\n"


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    with args.output.open("x", encoding="ascii") as f:
        f.write(build())
