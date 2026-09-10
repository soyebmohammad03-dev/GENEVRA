"""Lightweight, reproducible partitioning of learning strategies into
"strategy clusters" (Phase 9.5), plus population-level structure derived
from those clusters over time (Phase 9.4's diversity-hiding-structure
concern, and lineage-side persistence/turnover/survival).

Deliberately a from-scratch k-means (the only new dependency this needs
is numpy, already required) rather than pulling in scikit-learn for a
handful of 3-dimensional points. Cluster labels are integers with no
biological meaning: **a cluster is a "strategy cluster," never a
"species."**
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

import numpy as np
import numpy.typing as npt

from genevra.analysis.learning_strategy import LearningStrategy
from genevra.evolution.lineage import LineageEvent

_Float64Array = npt.NDArray[np.float64]
_IntArray = npt.NDArray[np.int64]


@dataclass(frozen=True)
class ClusterAssignment:
    """`labels[i]` is the strategy-cluster id assigned to `strategies[i]`.
    `inertia` is the sum of squared distances to each point's assigned
    centroid (k-means' own objective) — reported so a caller can judge
    fit quality, never used to claim statistical significance on its
    own."""

    labels: tuple[int, ...]
    centroids: tuple[tuple[float, ...], ...]
    k: int
    inertia: float
    method: str = "kmeans"


class KMeansClusterer:
    """Deterministic (given `rng`) Lloyd's-algorithm k-means over
    `LearningStrategy` vectors. `n_init` restarts pick the lowest-inertia
    result, since a single random initialization of k-means is not
    reproducible in the scientific sense (different seeds can converge to
    different local optima)."""

    def __init__(self, k: int, max_iter: int = 100, n_init: int = 5) -> None:
        if k < 1:
            raise ValueError("k must be >= 1")
        if max_iter < 1:
            raise ValueError("max_iter must be >= 1")
        if n_init < 1:
            raise ValueError("n_init must be >= 1")
        self.k = k
        self.max_iter = max_iter
        self.n_init = n_init

    def fit(
        self, strategies: Sequence[LearningStrategy], rng: np.random.Generator
    ) -> ClusterAssignment:
        points = np.stack([s.as_vector() for s in strategies]).astype(np.float64)
        n = len(points)
        k = min(self.k, n)
        if k < 1:
            raise ValueError("at least one strategy is required to cluster")

        best_labels: _IntArray | None = None
        best_centroids: _Float64Array | None = None
        best_inertia = float("inf")
        for _ in range(self.n_init):
            labels, centroids, inertia = _kmeans_once(points, k, self.max_iter, rng)
            if inertia < best_inertia:
                best_inertia, best_labels, best_centroids = inertia, labels, centroids

        assert best_labels is not None and best_centroids is not None
        return ClusterAssignment(
            labels=tuple(int(label) for label in best_labels),
            centroids=tuple(tuple(float(x) for x in row) for row in best_centroids),
            k=k,
            inertia=float(best_inertia),
        )


def _kmeans_once(
    points: _Float64Array, k: int, max_iter: int, rng: np.random.Generator
) -> tuple[_IntArray, _Float64Array, float]:
    n = len(points)
    centroid_indices = rng.choice(n, size=k, replace=False)
    centroids = points[centroid_indices].copy()
    labels = np.full(n, -1, dtype=np.int64)

    for _iteration in range(max_iter):
        distances = np.linalg.norm(points[:, None, :] - centroids[None, :, :], axis=2)
        new_labels = np.argmin(distances, axis=1)
        converged = np.array_equal(new_labels, labels)
        labels = new_labels
        for cluster_id in range(k):
            members = points[labels == cluster_id]
            if len(members) > 0:
                centroids[cluster_id] = members.mean(axis=0)
        if converged:
            break

    distances = np.linalg.norm(points - centroids[labels], axis=1)
    inertia = float(np.sum(distances**2))
    return labels, centroids, inertia


def select_k(
    strategies: Sequence[LearningStrategy],
    rng: np.random.Generator,
    k_candidates: Sequence[int] = (1, 2, 3, 4),
    improvement_threshold: float = 0.10,
) -> ClusterAssignment:
    """A simple, documented elbow heuristic for choosing how many strategy
    clusters a population naturally separates into: increase k from the
    smallest candidate as long as it reduces inertia by more than
    `improvement_threshold` (a fraction of the previous inertia);
    otherwise stop at the previous k. This is a heuristic, not a
    statistical model-selection test — treat the resulting `k` as a
    starting point for investigation, not proof of `k` distinct
    regimes."""
    candidates = sorted(set(k_candidates))
    if not candidates:
        raise ValueError("k_candidates must be non-empty")

    best = KMeansClusterer(candidates[0]).fit(strategies, rng)
    baseline_inertia = best.inertia
    for k in candidates[1:]:
        candidate = KMeansClusterer(k).fit(strategies, rng)
        if baseline_inertia <= 0:
            break
        # Improvement relative to the *baseline* (k=1) inertia, not the
        # previous step's — so diminishing marginal gains from splitting
        # an already well-separated cluster further are correctly seen as
        # small, instead of looking large purely because the previous
        # step's inertia was already tiny.
        improvement = (best.inertia - candidate.inertia) / baseline_inertia
        if improvement < improvement_threshold:
            break
        best = candidate
    return best


def strategy_frequencies(assignment: ClusterAssignment) -> dict[int, float]:
    """Fraction of the population in each strategy cluster — the
    structure a population mean learning rate can hide (Phase 9.4's
    "Strategy A / Strategy B" example)."""
    counts: dict[int, int] = {}
    for label in assignment.labels:
        counts[label] = counts.get(label, 0) + 1
    total = len(assignment.labels)
    return {label: count / total for label, count in counts.items()} if total else {}


@dataclass(frozen=True)
class StrategyLineageSummary:
    """Per-cluster lineage-side statistics, derived from `LineageEvent`
    records (Phase 9.4's persistence/turnover/lineage-survival
    requirements). `persistence` is the fraction of individuals in a
    cluster whose `reproduced` flag is set — a crude but genome-agnostic
    proxy for "did this strategy leave descendants," not a guarantee of
    long-run survival."""

    cluster_id: int
    num_individuals: int
    persistence: float
    generation_span: tuple[int, int]


def strategy_lineage_survival(
    events: Sequence[LineageEvent], clusterer: KMeansClusterer, rng: np.random.Generator
) -> tuple[StrategyLineageSummary, ...]:
    if not events:
        return ()
    strategies = [LearningStrategy(*event.learning_strategy) for event in events]
    assignment = clusterer.fit(strategies, rng)

    by_cluster: dict[int, list[LineageEvent]] = {}
    for event, label in zip(events, assignment.labels, strict=True):
        by_cluster.setdefault(label, []).append(event)

    summaries = []
    for cluster_id, members in sorted(by_cluster.items()):
        reproduced_fraction = float(np.mean([m.reproduced for m in members]))
        generations = [m.generation for m in members]
        summaries.append(
            StrategyLineageSummary(
                cluster_id=cluster_id,
                num_individuals=len(members),
                persistence=reproduced_fraction,
                generation_span=(min(generations), max(generations)),
            )
        )
    return tuple(summaries)


def strategy_turnover(
    events_by_generation: Sequence[Sequence[LineageEvent]],
    clusterer: KMeansClusterer,
    rng: np.random.Generator,
) -> list[float]:
    """Fraction of the dominant strategy cluster's population identity
    that changes from one generation's birth cohort to the next, measured
    as `1 - (fraction of generation g+1 sharing g's most common cluster
    centroid's nearest label)`. Callers pass one list of `LineageEvent`s
    per generation (e.g. grouped by `.generation`); returns one turnover
    value per consecutive pair, so `len(result) == len(events_by_generation) - 1`."""
    if len(events_by_generation) < 2:
        return []
    all_events = [e for gen in events_by_generation for e in gen]
    if not all_events:
        return []
    strategies = [LearningStrategy(*e.learning_strategy) for e in all_events]
    assignment = clusterer.fit(strategies, rng)

    labels_by_generation: list[list[int]] = []
    offset = 0
    for gen_events in events_by_generation:
        n = len(gen_events)
        labels_by_generation.append(list(assignment.labels[offset : offset + n]))
        offset += n

    turnovers = []
    # Deliberately unequal-length zip: pairs consecutive generations, so the
    # trailing generation has no "next" partner (`strict=True` would reject this).
    for previous, current in zip(labels_by_generation, labels_by_generation[1:], strict=False):
        if not previous or not current:
            turnovers.append(0.0)
            continue
        dominant_previous = max(set(previous), key=previous.count)
        share_retained = current.count(dominant_previous) / len(current)
        turnovers.append(1.0 - share_retained)
    return turnovers


__all__ = [
    "ClusterAssignment",
    "KMeansClusterer",
    "select_k",
    "strategy_frequencies",
    "StrategyLineageSummary",
    "strategy_lineage_survival",
    "strategy_turnover",
]
