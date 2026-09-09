"""Lightweight, reproducible plots over stored experiment results.

Kept separate from simulation and analysis: every function here takes
already-computed data (a trajectory's list of generation dicts, an
`EcologicalSnapshot` sequence, `EvolvabilitySample`s) and returns a
matplotlib `Figure` — it never runs a simulation itself. A figure made
from a stored `ExperimentResult` is therefore reproducible: re-plot it any
time from the saved JSON, without re-running anything.

`matplotlib` is an optional dependency (`pip install -e ".[viz]"`) and is
imported lazily inside each function, so the core `genevra` package (and
every other module in it) never requires it.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING, Any, cast

if TYPE_CHECKING:
    from matplotlib.figure import Figure

_MISSING_MATPLOTLIB = (
    'matplotlib is required for genevra.visualization. Install it with: pip install -e ".[viz]"'
)


def _require_matplotlib() -> Any:
    try:
        import matplotlib.pyplot as plt
    except ImportError as exc:  # pragma: no cover - exercised only without the optional dep
        raise ImportError(_MISSING_MATPLOTLIB) from exc
    return plt


def _line_plot(
    x: Sequence[float], y: Sequence[float], *, xlabel: str, ylabel: str, title: str
) -> Figure:
    plt = _require_matplotlib()
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.plot(x, y, marker="o", markersize=3)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    fig.tight_layout()
    return cast("Figure", fig)


def plot_fitness_trajectory(trajectory: Sequence[dict[str, Any]]) -> Figure:
    generations = [g["generation"] for g in trajectory]
    means = [g["fitness_summary"]["mean"] for g in trajectory]
    return _line_plot(
        generations, means, xlabel="generation", ylabel="mean fitness", title="Fitness"
    )


def plot_novelty_trajectory(trajectory: Sequence[dict[str, Any]]) -> Figure:
    plt = _require_matplotlib()
    generations = [g["generation"] for g in trajectory]
    cumulative = [g["mean_novelty"] for g in trajectory]
    instantaneous = [g["instantaneous_novelty"] for g in trajectory]
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.plot(generations, cumulative, marker="o", markersize=3, label="cumulative (archive)")
    ax.plot(
        generations,
        instantaneous,
        marker="o",
        markersize=3,
        label="instantaneous (this generation)",
    )
    ax.set_xlabel("generation")
    ax.set_ylabel("novelty")
    ax.set_title("Novelty")
    ax.legend()
    fig.tight_layout()
    return cast("Figure", fig)


def plot_diversity_trajectory(trajectory: Sequence[dict[str, Any]]) -> Figure:
    plt = _require_matplotlib()
    generations = [g["generation"] for g in trajectory]
    genotypic = [g["genotypic_diversity"] for g in trajectory]
    behavioral = [g["behavioral_diversity"] for g in trajectory]
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.plot(generations, genotypic, marker="o", markersize=3, label="genotypic")
    ax.plot(generations, behavioral, marker="o", markersize=3, label="behavioral")
    ax.set_xlabel("generation")
    ax.set_ylabel("mean pairwise distance")
    ax.set_title("Diversity")
    ax.legend()
    fig.tight_layout()
    return cast("Figure", fig)


def plot_population_size(snapshots: Sequence[Any]) -> Figure:
    steps = [s.step for s in snapshots]
    sizes = [s.population_size for s in snapshots]
    return _line_plot(
        steps, sizes, xlabel="step", ylabel="population size", title="Population size"
    )


def plot_lineage_survival(summaries: Sequence[Any]) -> Figure:
    plt = _require_matplotlib()
    sizes = sorted((s.size for s in summaries), reverse=True)
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.bar(range(len(sizes)), sizes)
    ax.set_xlabel("lineage (ranked by size)")
    ax.set_ylabel("number of individuals")
    ax.set_title("Lineage survival")
    fig.tight_layout()
    return cast("Figure", fig)


def plot_evolvability_over_time(samples: Sequence[Any]) -> Figure:
    _require_matplotlib()
    by_generation: dict[int, list[float]] = {}
    for sample in samples:
        by_generation.setdefault(sample.generation, []).append(
            sample.report.mean_behavioral_distance
        )
    generations = sorted(by_generation)
    means = [sum(by_generation[g]) / len(by_generation[g]) for g in generations]
    return _line_plot(
        generations,
        means,
        xlabel="generation",
        ylabel="mean behavioral distance",
        title="Evolvability",
    )
