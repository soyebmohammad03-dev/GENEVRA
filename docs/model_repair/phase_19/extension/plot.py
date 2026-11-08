"""Plot verified high-budget coverage and false-certification counts."""

import json
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
from matplotlib import pyplot as plt  # noqa: E402

results, destination = map(Path, sys.argv[1:])
summary = json.loads(results.read_text())["summary"]
methods = {
    "reachable_only": "Reachable only",
    "equal_envelope": "Equal-spend envelope",
    "planned_envelope": "Planned envelope",
    "full_hidden_support": "Unrestricted hidden tail",
}
colors = ("#a14b37", "#176c76", "#4873a0", "#79798e")
rows = {
    (row["case"], row["method"]): row
    for row in summary
    if row["budget"] == 32768 and row["method"] in methods
}
cases = list(dict.fromkeys(case for case, _ in rows))
plt.rcParams["svg.hashsalt"] = "genevra-coverage-envelope-v1"
plt.rcParams["svg.fonttype"] = "none"
figure, axes = plt.subplots(1, 2, figsize=(9, 4.8), sharey=True)
for ax, (metric, title) in zip(
    axes,
    [
        ("coverage_with_precision", "A  Covered and precise"),
        ("false_certificate", "B  False certificates"),
    ],
    strict=True,
):
    for j, (method, label) in enumerate(methods.items()):
        x = [100 * rows[case, method]["rates"][metric]["rate"] for case in cases]
        ax.barh(
            [i + (j - 1.5) * 0.18 for i in range(len(cases))],
            x,
            height=0.16,
            color=colors[j],
            label=label,
        )
    ax.set(
        xlim=(0, 101),
        xlabel="Replicates (%)",
        yticks=range(len(cases)),
        yticklabels=[x.replace("_", " ").capitalize() for x in cases],
        ylim=(len(cases) - 0.5, -0.5),
    )
    ax.set_title(title, loc="left", weight="bold", fontsize=11)
    ax.tick_params(labelsize=8)
    ax.spines[["top", "right", "left"]].set_visible(False)
axes[0].legend(loc="upper left", bbox_to_anchor=(0, -0.20), ncol=2, frameon=False, fontsize=8)
figure.text(0.17, 0.96, "Coverage-envelope benchmark", fontsize=16, weight="bold")
figure.text(0.17, 0.90, "32,768 charged units · 512 synthetic replicates per case", fontsize=10)
figure.subplots_adjust(left=0.18, right=0.98, top=0.79, bottom=0.22, wspace=0.12)
svg = destination.with_suffix(".svg")
figure.savefig(svg, metadata={"Date": None})
svg.write_text("\n".join(line.rstrip() for line in svg.read_text().splitlines()) + "\n")
figure.savefig(destination.with_suffix(".png"), dpi=240)
