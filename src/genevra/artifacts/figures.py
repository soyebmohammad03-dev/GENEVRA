"""Phase 14.3: publication-style figures over stored GENEVRA data.

Every function takes already-computed data (a trajectory's list of
generation dicts, sampled measurements) and returns `FigureMetadata` for
one saved figure — the same "never runs a simulation itself" contract as
`genevra.visualization`, extended with the metadata sidecar and caption
from `genevra.artifacts.style`/`genevra.artifacts.captions`.

Phase 14.3 explicitly does not require all 20 listed figure types for
every experiment. `select_available_figures` inspects what data is
present and returns only the figure kinds it can honestly produce;
`docs/figure_system.md` documents every skipped type and why.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import TYPE_CHECKING, Any

from genevra.artifacts.captions import (
    bar_caption,
    forest_plot_caption,
    histogram_caption,
    scatter_caption,
    trajectory_caption,
)
from genevra.artifacts.style import FigureMetadata, apply_style, require_matplotlib, save_figure

if TYPE_CHECKING:
    pass

_LEARNING_GENE_NAMES = ("learning_rate", "plasticity_gate", "decay")


def plot_fitness_trajectory(
    trajectory: Sequence[Mapping[str, Any]], output_dir: Path, experiment_id: str
) -> FigureMetadata:
    apply_style()
    plt = require_matplotlib()
    generations = [g["generation"] for g in trajectory]
    means = [g["fitness_summary"]["mean"] for g in trajectory]
    fig, ax = plt.subplots()
    ax.plot(generations, means, marker="o", markersize=3)
    ax.set_xlabel("generation")
    ax.set_ylabel("mean fitness")
    ax.set_title("Fitness trajectory")
    fig.tight_layout()
    return save_figure(
        fig,
        output_dir,
        figure_id="fitness_trajectory",
        experiment_id=experiment_id,
        data_source="ExperimentResult.trajectory[*].fitness_summary.mean",
        metrics=("fitness_summary.mean",),
        caption=trajectory_caption("Mean population fitness", len(trajectory), experiment_id),
        limitations=(
            "One realized run; no cross-seed uncertainty band unless multiple seeds are pooled."
        ),
    )


def plot_novelty_trajectory(
    trajectory: Sequence[Mapping[str, Any]], output_dir: Path, experiment_id: str
) -> FigureMetadata:
    apply_style()
    plt = require_matplotlib()
    generations = [g["generation"] for g in trajectory]
    fig, ax = plt.subplots()
    ax.plot(
        generations,
        [g["mean_novelty"] for g in trajectory],
        marker="o",
        markersize=3,
        label="cumulative (archive)",
    )
    ax.plot(
        generations,
        [g["instantaneous_novelty"] for g in trajectory],
        marker="o",
        markersize=3,
        label="instantaneous (this generation)",
    )
    ax.set_xlabel("generation")
    ax.set_ylabel("novelty")
    ax.set_title("Novelty trajectory")
    ax.legend()
    fig.tight_layout()
    return save_figure(
        fig,
        output_dir,
        figure_id="novelty_trajectory",
        experiment_id=experiment_id,
        data_source="ExperimentResult.trajectory[*].{mean_novelty,instantaneous_novelty}",
        metrics=("mean_novelty", "instantaneous_novelty"),
        caption=trajectory_caption(
            "Cumulative and instantaneous novelty", len(trajectory), experiment_id
        ),
        limitations=(
            "Novelty is relative to this run's own archive/population, not an absolute scale."
        ),
    )


def plot_diversity_trajectory(
    trajectory: Sequence[Mapping[str, Any]], output_dir: Path, experiment_id: str
) -> FigureMetadata:
    apply_style()
    plt = require_matplotlib()
    generations = [g["generation"] for g in trajectory]
    fig, ax = plt.subplots()
    ax.plot(
        generations,
        [g["genotypic_diversity"] for g in trajectory],
        marker="o",
        markersize=3,
        label="genotypic",
    )
    ax.plot(
        generations,
        [g["behavioral_diversity"] for g in trajectory],
        marker="o",
        markersize=3,
        label="behavioral",
    )
    ax.set_xlabel("generation")
    ax.set_ylabel("mean pairwise distance")
    ax.set_title("Diversity trajectory")
    ax.legend()
    fig.tight_layout()
    return save_figure(
        fig,
        output_dir,
        figure_id="diversity_trajectory",
        experiment_id=experiment_id,
        data_source="ExperimentResult.trajectory[*].{genotypic_diversity,behavioral_diversity}",
        metrics=("genotypic_diversity", "behavioral_diversity"),
        caption=trajectory_caption(
            "Genotypic and behavioral diversity", len(trajectory), experiment_id
        ),
        limitations=(
            "Diversity may be computed on a capped random pair sample; see diversity_max_pairs."
        ),
    )


def plot_learning_strategy_trajectory(
    trajectory: Sequence[Mapping[str, Any]], output_dir: Path, experiment_id: str
) -> FigureMetadata | None:
    """`None` when no generation carries RESEARCH-level `learning_gene_stats`
    — the figure-selection system's job, not a caller's, to notice this."""
    apply_style()
    generations = []
    values: dict[str, list[float]] = {name: [] for name in _LEARNING_GENE_NAMES}
    for g in trajectory:
        stats = g.get("learning_gene_stats")
        if not stats:
            continue
        generations.append(g["generation"])
        for name, stat in zip(_LEARNING_GENE_NAMES, stats, strict=False):
            values[name].append(stat["mean"])
    if not generations:
        return None
    plt = require_matplotlib()
    fig, ax = plt.subplots()
    for name in _LEARNING_GENE_NAMES:
        if len(values[name]) == len(generations):
            ax.plot(generations, values[name], marker="o", markersize=3, label=name)
    ax.set_xlabel("generation")
    ax.set_ylabel("mean gene value")
    ax.set_title("Learning-strategy gene trajectory")
    ax.legend()
    fig.tight_layout()
    return save_figure(
        fig,
        output_dir,
        figure_id="learning_strategy_trajectory",
        experiment_id=experiment_id,
        data_source="ExperimentResult.trajectory[*].learning_gene_stats (RESEARCH metrics level)",
        metrics=_LEARNING_GENE_NAMES,
        caption=trajectory_caption(
            "Mean learning_rate/plasticity_gate/decay", len(generations), experiment_id
        ),
        limitations="Mean across the population; bimodal strategy splits are not visible here.",
    )


def plot_robustness_vs_evolvability(
    robustness_values: Sequence[float],
    evolvability_values: Sequence[float],
    output_dir: Path,
    experiment_id: str,
) -> FigureMetadata:
    apply_style()
    plt = require_matplotlib()
    fig, ax = plt.subplots()
    ax.scatter(robustness_values, evolvability_values, s=20)
    ax.set_xlabel("genetic robustness (mean behavioral distance under mutation)")
    ax.set_ylabel("evolvability (mean behavioral distance, mutational neighborhood)")
    ax.set_title("Robustness vs. evolvability")
    fig.tight_layout()
    return save_figure(
        fig,
        output_dir,
        figure_id="robustness_vs_evolvability",
        experiment_id=experiment_id,
        data_source=(
            "genevra.mechanisms.robustness / genevra.metrics.evolvability, sampled genotypes"
        ),
        metrics=("genetic_robustness_mean", "evolvability_mean_behavioral_distance"),
        caption=scatter_caption("robustness", "evolvability", len(robustness_values)),
        limitations=(
            "Association only (Pearson r reported separately); no causal direction is implied."
        ),
    )


def plot_plasticity_benefit_vs_cost(
    associations: Mapping[str, float | None], output_dir: Path, experiment_id: str
) -> FigureMetadata:
    apply_style()
    plt = require_matplotlib()
    labels = list(associations)
    values = [associations[k] if associations[k] is not None else 0.0 for k in labels]
    colors = ["#4c72b0" if associations[k] is not None else "#bbbbbb" for k in labels]
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.barh(range(len(labels)), values, color=colors)
    ax.set_yticks(range(len(labels)))
    ax.set_yticklabels(labels, fontsize=8)
    ax.axvline(0.0, color="black", linewidth=0.8)
    ax.set_xlabel("Pearson correlation with plasticity_gate")
    ax.set_title("Plasticity: benefit/cost associations")
    fig.tight_layout()
    return save_figure(
        fig,
        output_dir,
        figure_id="plasticity_benefit_vs_cost",
        experiment_id=experiment_id,
        data_source="genevra.mechanisms.plasticity_cost.PlasticityCostReport.associations",
        metrics=tuple(labels),
        caption=bar_caption("associated trait", "Pearson correlation", len(labels)),
        limitations=(
            "Gray bars mark associations with insufficient paired data (< 3 observations), "
            "shown as zero."
        ),
    )


def plot_mutational_neighborhood_distribution(
    behavioral_distances: Sequence[float], output_dir: Path, experiment_id: str
) -> FigureMetadata:
    apply_style()
    plt = require_matplotlib()
    fig, ax = plt.subplots()
    ax.hist(behavioral_distances, bins=min(20, max(3, len(behavioral_distances) // 2)))
    ax.set_xlabel("behavioral distance from baseline")
    ax.set_ylabel("count")
    ax.set_title("Mutational-neighborhood behavioral distance")
    fig.tight_layout()
    return save_figure(
        fig,
        output_dir,
        figure_id="mutational_neighborhood_distribution",
        experiment_id=experiment_id,
        data_source="genevra.mechanisms.mutational_landscape.NeighborhoodSample.behavioral_distances",
        metrics=("behavioral_distance",),
        caption=histogram_caption("behavioral distance", len(behavioral_distances)),
        limitations=(
            "One-step sampled neighborhood at fixed sample size; not exhaustive enumeration."
        ),
    )


def plot_innovation_event_timeline(
    events: Sequence[Mapping[str, Any]], output_dir: Path, experiment_id: str
) -> FigureMetadata | None:
    if not events:
        return None
    apply_style()
    plt = require_matplotlib()
    generations = [e["generation"] for e in events]
    novelty = [e["novelty_score"] for e in events]
    descendants = [e.get("descendant_count", 0) for e in events]
    fig, ax = plt.subplots()
    scatter = ax.scatter(generations, novelty, s=[10 + 4 * d for d in descendants], alpha=0.7)
    ax.set_xlabel("generation")
    ax.set_ylabel("novelty score (z-scored strategy outlier magnitude)")
    ax.set_title("Innovation event timeline")
    fig.tight_layout()
    _ = scatter
    return save_figure(
        fig,
        output_dir,
        figure_id="innovation_event_timeline",
        experiment_id=experiment_id,
        data_source="genevra.innovation.events.InnovationEvent[*]",
        metrics=("generation", "novelty_score", "descendant_count"),
        caption=scatter_caption("generation", "novelty score", len(events))
        + " Marker size scales with descendant_count.",
        limitations=(
            "Innovation events are detected as learning-strategy outliers only, not "
            "general behavioral novelty."
        ),
    )


def plot_effect_size_forest(
    effects: Sequence[Mapping[str, Any]],
    output_dir: Path,
    experiment_id: str,
    ci_level: float = 0.95,
) -> FigureMetadata | None:
    """`effects`: sequence of `{"label": str, "estimate": float, "ci_low":
    float | None, "ci_high": float | None}`."""
    if not effects:
        return None
    apply_style()
    plt = require_matplotlib()
    fig, ax = plt.subplots(figsize=(6, 0.6 * len(effects) + 1.5))
    ys = range(len(effects))
    estimates = [e["estimate"] for e in effects]
    labels = [e["label"] for e in effects]
    lows = [e.get("ci_low") for e in effects]
    highs = [e.get("ci_high") for e in effects]
    for y, estimate, low, high in zip(ys, estimates, lows, highs, strict=True):
        if low is not None and high is not None:
            ax.plot([low, high], [y, y], color="#4c72b0", linewidth=1.5)
        ax.plot(estimate, y, "o", color="#4c72b0")
    ax.axvline(0.0, color="black", linewidth=0.8, linestyle="--")
    ax.set_yticks(list(ys))
    ax.set_yticklabels(labels, fontsize=8)
    ax.set_xlabel("effect size")
    ax.set_title("Effect sizes")
    fig.tight_layout()
    return save_figure(
        fig,
        output_dir,
        figure_id="effect_size_forest",
        experiment_id=experiment_id,
        data_source="genevra.analysis.aggregation effect-size/bootstrap results",
        metrics=("effect_size",),
        caption=forest_plot_caption(len(effects), ci_level),
        limitations=(
            "A point with no drawn interval means the interval could not be computed, "
            "not that it is zero-width."
        ),
    )


def plot_overview_panel(
    trajectory: Sequence[Mapping[str, Any]], output_dir: Path, experiment_id: str
) -> FigureMetadata:
    """Phase 14.7: one 2x2 multi-panel figure — A. fitness, B. novelty,
    C. diversity, D. learning-strategy diversity (skipped as a blank
    panel with a note when RESEARCH-level gene stats were not recorded).
    Each panel answers a distinct question already asked by this
    module's single-metric figures; this is not decoration."""
    apply_style()
    plt = require_matplotlib()
    generations = [g["generation"] for g in trajectory]
    fig, axes = plt.subplots(2, 2, figsize=(9, 6))

    axes[0, 0].plot([g["fitness_summary"]["mean"] for g in trajectory], marker="o", markersize=2)
    axes[0, 0].set_title("A. Fitness")
    axes[0, 0].set_xlabel("generation")
    axes[0, 0].set_ylabel("mean fitness")

    axes[0, 1].plot(
        [g["instantaneous_novelty"] for g in trajectory],
        marker="o",
        markersize=2,
        color="tab:orange",
    )
    axes[0, 1].set_title("B. Instantaneous novelty")
    axes[0, 1].set_xlabel("generation")

    axes[1, 0].plot(
        [g["genotypic_diversity"] for g in trajectory], marker="o", markersize=2, label="genotypic"
    )
    axes[1, 0].plot(
        [g["behavioral_diversity"] for g in trajectory],
        marker="o",
        markersize=2,
        label="behavioral",
    )
    axes[1, 0].set_title("C. Diversity")
    axes[1, 0].set_xlabel("generation")
    axes[1, 0].legend(fontsize=7)

    gate_values = [
        g["learning_gene_stats"][1]["mean"] for g in trajectory if g.get("learning_gene_stats")
    ]
    if gate_values:
        axes[1, 1].plot(gate_values, marker="o", markersize=2, color="tab:green")
        axes[1, 1].set_title("D. Mean plasticity_gate")
    else:
        axes[1, 1].text(
            0.5, 0.5, "no RESEARCH-level\nlearning_gene_stats", ha="center", va="center"
        )
        axes[1, 1].set_title("D. Learning-strategy diversity (unavailable)")
    axes[1, 1].set_xlabel("generation")

    fig.suptitle(f"Overview: {experiment_id}")
    fig.tight_layout()
    return save_figure(
        fig,
        output_dir,
        figure_id="overview_panel",
        experiment_id=experiment_id,
        data_source="ExperimentResult.trajectory",
        metrics=(
            "fitness_summary.mean",
            "instantaneous_novelty",
            "genotypic_diversity",
            "behavioral_diversity",
        ),
        caption=(
            f"Four-panel overview of {len(generations)} generations for experiment "
            f"'{experiment_id}': (A) fitness, (B) instantaneous novelty, (C) diversity, "
            "(D) mean plasticity_gate when available."
        ),
        limitations="Composed from the same single-run trajectory as the individual figures above.",
    )


def plot_population_size_trajectory(
    steps: Sequence[int],
    population_sizes: Sequence[int],
    output_dir: Path,
    experiment_id: str,
) -> FigureMetadata:
    """Phase 16.11: population size over a `ContinuousEvolutionEngine`
    run's `EcologicalSnapshot` history (or a `Metapopulation`'s per-patch
    history, summed/plotted per patch by the caller)."""
    apply_style()
    plt = require_matplotlib()
    fig, ax = plt.subplots()
    ax.plot(list(steps), list(population_sizes), marker="o", markersize=3)
    ax.set_xlabel("step")
    ax.set_ylabel("population size")
    ax.set_title("Population size trajectory")
    fig.tight_layout()
    return save_figure(
        fig,
        output_dir,
        figure_id="population_size_trajectory",
        experiment_id=experiment_id,
        data_source="EcologicalSnapshot.population_size",
        metrics=("population_size",),
        caption=trajectory_caption("Population size", len(steps), experiment_id),
        limitations=(
            "One realized run; a `ContinuousEvolutionEngine`'s population size can "
            "reflect capacity limits (max_population) as much as ecological dynamics."
        ),
    )


def plot_replication_consistency(
    seeds: Sequence[int],
    effects: Sequence[float],
    output_dir: Path,
    experiment_id: str,
) -> FigureMetadata:
    """Phase 16.11/16.8: one point per independent seed's effect
    estimate, with a zero-effect reference line — makes seed-to-seed
    sign disagreement visible rather than hidden behind a pooled p-value
    (`genevra.population_analysis.replication_consistency`)."""
    apply_style()
    plt = require_matplotlib()
    fig, ax = plt.subplots()
    ax.axhline(0.0, linestyle="--", linewidth=1, alpha=0.6)
    ax.scatter(list(seeds), list(effects))
    ax.set_xlabel("seed")
    ax.set_ylabel("effect estimate")
    ax.set_title("Replication consistency across seeds")
    fig.tight_layout()
    return save_figure(
        fig,
        output_dir,
        figure_id="replication_consistency",
        experiment_id=experiment_id,
        data_source="ReplicationConsistencyReport.per_seed_effect",
        metrics=("per_seed_effect",),
        caption=scatter_caption("seed", "effect estimate", len(seeds)),
        limitations=(
            "Each point is one independent seed's own effect estimate; this plot shows "
            "sign/magnitude agreement across seeds, not a pooled significance test."
        ),
    )


__all__ = [
    "plot_fitness_trajectory",
    "plot_novelty_trajectory",
    "plot_diversity_trajectory",
    "plot_learning_strategy_trajectory",
    "plot_robustness_vs_evolvability",
    "plot_plasticity_benefit_vs_cost",
    "plot_mutational_neighborhood_distribution",
    "plot_innovation_event_timeline",
    "plot_effect_size_forest",
    "plot_overview_panel",
    "plot_population_size_trajectory",
    "plot_replication_consistency",
]
