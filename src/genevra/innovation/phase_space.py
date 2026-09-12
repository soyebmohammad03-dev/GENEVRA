"""Phase 12.8: a multidimensional phase-space representation of
evolutionary dynamics, and reproducible dimensionality reduction.

Dimensionality reduction, when used, is mean-centered PCA computed via
`numpy.linalg.svd` — a deterministic, dependency-free method (no
scikit-learn), fully specified by `PhaseSpaceProjection.method`,
`n_components`, and the per-dimension `explained_variance_ratio` it
reports. This module never reduces dimensionality "for a nicer plot"
without reporting the method and how much variance survived the
projection.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

import numpy as np


@dataclass(frozen=True)
class PhaseSpaceTrajectory:
    dimension_names: tuple[str, ...]
    generations: tuple[int, ...]
    matrix: tuple[tuple[float, ...], ...]
    """`matrix[i]` is the point at `generations[i]`, one value per
    `dimension_names` entry, in that order."""

    def to_dict(self) -> dict[str, Any]:
        return {
            "dimension_names": list(self.dimension_names),
            "generations": list(self.generations),
            "matrix": [list(row) for row in self.matrix],
        }


def build_phase_space_trajectory(
    metric_series: Mapping[str, Sequence[float]], generations: Sequence[int]
) -> PhaseSpaceTrajectory:
    """`metric_series` maps a dimension name to its per-generation values;
    every series must be the same length as `generations` — mismatched
    lengths raise rather than silently truncating/padding, since a
    phase-space point with a dimension missing at some generations is not
    a well-defined point."""
    if not metric_series:
        raise ValueError("at least one dimension is required")
    names = tuple(metric_series)
    for name in names:
        if len(metric_series[name]) != len(generations):
            raise ValueError(
                f"dimension {name!r} has {len(metric_series[name])} values, "
                f"expected {len(generations)} (one per generation)"
            )
    columns = [np.asarray(metric_series[name], dtype=np.float64) for name in names]
    matrix = np.stack(columns, axis=1) if columns else np.empty((len(generations), 0))
    return PhaseSpaceTrajectory(
        dimension_names=names,
        generations=tuple(generations),
        matrix=tuple(tuple(float(x) for x in row) for row in matrix),
    )


@dataclass(frozen=True)
class PhaseSpaceProjection:
    method: str
    n_components: int
    explained_variance_ratio: tuple[float, ...]
    projected: tuple[tuple[float, ...], ...]
    note: str = (
        "Mean-centered PCA via numpy.linalg.svd — a deterministic, exactly reproducible "
        "projection, reported alongside explained_variance_ratio so a low-variance "
        "projection is never presented without that context. Not used to claim any "
        "biological/behavioral meaning for the resulting axes beyond 'directions of "
        "maximal variance across the requested dimensions.'"
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "method": self.method,
            "n_components": self.n_components,
            "explained_variance_ratio": list(self.explained_variance_ratio),
            "projected": [list(row) for row in self.projected],
            "note": self.note,
        }


def project_phase_space(
    trajectory: PhaseSpaceTrajectory, n_components: int = 2
) -> PhaseSpaceProjection:
    matrix = np.asarray(trajectory.matrix, dtype=np.float64)
    n_points, n_dims = matrix.shape
    if n_points == 0 or n_dims == 0:
        raise ValueError("trajectory must have at least one point and one dimension")
    n_components = min(n_components, n_dims, max(n_points - 1, 1))

    centered = matrix - matrix.mean(axis=0, keepdims=True)
    # SVD-based PCA: singular values relate to eigenvalues of the
    # covariance matrix by singular_value^2 / (n-1); deterministic given
    # the input, no random initialization anywhere in this path.
    _u, singular_values, v_t = np.linalg.svd(centered, full_matrices=False)
    variances = (singular_values**2) / max(n_points - 1, 1)
    total_variance = float(variances.sum())
    ratios = tuple(
        float(v / total_variance) if total_variance > 0 else 0.0 for v in variances[:n_components]
    )
    components = v_t[:n_components]
    projected = centered @ components.T

    return PhaseSpaceProjection(
        method="PCA (mean-centered, numpy.linalg.svd)",
        n_components=n_components,
        explained_variance_ratio=ratios,
        projected=tuple(tuple(float(x) for x in row) for row in projected),
    )


__all__ = [
    "PhaseSpaceTrajectory",
    "build_phase_space_trajectory",
    "PhaseSpaceProjection",
    "project_phase_space",
]
