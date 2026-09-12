"""Phase 14.6: conservative, template-only caption generation.

Every function here describes what is plotted, the axes, condition(s),
sample size, and how uncertainty (if any) is represented — never a
conclusion ("X causes Y", "evolution favors Z"). No function in this
module accepts or emits free-text conclusions; the only inputs are the
structural facts already available at figure-generation time.
"""

from __future__ import annotations


def trajectory_caption(metric_label: str, n_generations: int, experiment_id: str) -> str:
    return (
        f"{metric_label} across {n_generations} generations for experiment "
        f"'{experiment_id}'. One value per generation from the stored trajectory; "
        "no smoothing or interpolation is applied."
    )


def scatter_caption(x_label: str, y_label: str, n_points: int) -> str:
    return (
        f"{y_label} plotted against {x_label} across {n_points} sampled genotypes. "
        "Each point is one independently sampled genotype; no trend line is fit "
        "unless explicitly noted."
    )


def bar_caption(category_label: str, value_label: str, n_categories: int) -> str:
    return (
        f"{value_label} by {category_label} across {n_categories} categories. "
        "Bars show point estimates only; see the accompanying table for sample "
        "sizes and any confidence intervals."
    )


def histogram_caption(value_label: str, n_samples: int) -> str:
    return (
        f"Distribution of {value_label} across {n_samples} sampled mutants. "
        "Each observation is one independently sampled mutant; n_samples is "
        "reported here rather than assumed from bin heights."
    )


def forest_plot_caption(n_effects: int, ci_level: float) -> str:
    return (
        f"Point estimate and {ci_level:.0%} confidence interval for {n_effects} effect "
        "size(s). A point-estimate label with no interval indicates the interval could "
        "not be computed (e.g. insufficient samples), not that the effect is exact."
    )


__all__ = [
    "trajectory_caption",
    "scatter_caption",
    "bar_caption",
    "histogram_caption",
    "forest_plot_caption",
]
