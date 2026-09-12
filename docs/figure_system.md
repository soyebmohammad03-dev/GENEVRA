# Figure system (Phase 14.2-14.7)

`genevra.artifacts.figures` produces publication-style figures from
already-computed data — a `Trajectory.to_dict()`-shaped list, sampled
robustness/evolvability/mutational-landscape/innovation-event data — the
same "never runs a simulation itself" contract `genevra.visualization`
already established. It extends, rather than replaces, that module:
`genevra.visualization` stays the lightweight single-purpose plotting
surface; `genevra.artifacts.figures` adds the metadata sidecar, shared
style, and the newer figure types Phase 13's analyzers make possible.

## Style

`genevra.artifacts.style.apply_style()` sets one consistent
`matplotlib` style (fixed figure size/DPI/font sizes, no top/right
spines, light grid) — called by every figure function in this package.
No 3D plots, no gradients, no decorative icons, no screenshots: Phase
14.13's explicit prohibitions.

## Figure metadata (Phase 14.5)

Every figure function returns a `FigureMetadata` (via
`genevra.artifacts.style.save_figure`) and writes a `<figure_id>.json`
sidecar alongside the image: `figure_id`, `experiment_id`, `data_source`
(exactly which stored field(s) fed the plot), `metrics`,
`analysis_version`, `seed_policy`, `creation_timestamp`, `git_commit`
(best-effort `git rev-parse HEAD`, `None` outside a git checkout),
`parameters`, `caption`, `limitations`. This is what lets a figure be
regenerated exactly later, per Phase 14.5's requirement.

## Captions (Phase 14.6)

`genevra.artifacts.captions` builds every caption from pure templates:
what is plotted, the axes, sample size, how uncertainty is represented.
No caption function accepts free-text and no caption states a
conclusion — see the module docstring's GOOD/BAD examples, which mirror
the ones in the Phase 14 spec.

## Implemented figure types (10 of the 20 listed in the spec)

The spec explicitly says not to force all 20 for every experiment and to
select figures based on available data. GENEVRA currently implements:

1. `plot_fitness_trajectory` — mean fitness per generation.
2. `plot_novelty_trajectory` — cumulative + instantaneous novelty.
3. `plot_diversity_trajectory` — genotypic + behavioral diversity (one
   figure, matching `genevra.visualization.plot_diversity_trajectory`).
4. `plot_learning_strategy_trajectory` — mean learning_rate/
   plasticity_gate/decay per generation; returns `None` (the
   figure-selection contract) when the stored trajectory has no
   RESEARCH-level `learning_gene_stats`.
5. `plot_robustness_vs_evolvability` — scatter over sampled genotypes.
6. `plot_plasticity_benefit_vs_cost` — bar chart of
   `PlasticityCostReport.associations`; associations with insufficient
   paired data are drawn gray at zero, never omitted silently.
7. `plot_mutational_neighborhood_distribution` — histogram of one-step
   behavioral distances.
8. `plot_innovation_event_timeline` — generation vs. novelty_score
   scatter, marker size scaling with descendant_count; `None` when there
   are no detected events.
9. `plot_effect_size_forest` — point estimate + CI per named effect;
   `None` when the effect list is empty, and a point with no drawn
   interval is explicitly captioned as "could not be computed," never as
   zero-width.
10. `plot_overview_panel` — one 2×2 multi-panel figure (Phase 14.7):
    (A) fitness, (B) instantaneous novelty, (C) diversity, (D) mean
    `plasticity_gate` when RESEARCH-level gene stats exist, otherwise an
    explicit "unavailable" panel rather than a fabricated one.

## Skipped figure types, and why

The remaining ten types from the Phase 14.3 list are not implemented in
this phase because GENEVRA does not yet produce the underlying data in a
form worth plotting, or the type duplicates one already covered:

- **Lineage trees / branching** — `LineageTracker` records ancestry, but
  a genuinely useful tree rendering (vs. a cluttered node-link diagram at
  population scale) needs a dedicated layout, deferred rather than
  shipped as a placeholder.
- **Environmental volatility × strategy heatmap** — needs a 2D sweep
  over volatility levels and strategy clusters that no existing
  experiment matrix currently runs by default.
- **Generalization matrix** — `GeneralizationProfile` currently has 4
  categories for 1 genome; a matrix figure is only informative across
  many genomes/conditions, which is future comparison-runner work, not a
  figure-layer gap.
- **Strategy-space trajectory** — needs a 2D/3D projection of
  `LearningStrategy` vectors over time; deferred pending a documented,
  reproducible dimensionality-reduction choice (Phase 12.8's own
  requirement not to reduce dimensions "merely for attractive plots").
- **Phase/regime map** — depends on `genevra.mechanisms.regime`'s new
  per-generation labels being run over a real multi-condition experiment
  first; not yet exercised at that scale.
- **Innovation persistence curves** — `genevra.innovation.activity`
  computes persistence-adjacent statistics already reported in text form
  by `genevra innovation`/`genevra activity`; a dedicated curve figure is
  a natural next addition once a longer run is available to plot.
- **Replication consistency plot** — depends on
  `genevra.discovery.replication`'s output shape, which this phase did
  not wire into the figure layer to avoid speculative plumbing ahead of
  an actual replication CLI use case.
- **Open-endedness metric trajectories** as a *dedicated* figure —
  covered today by `plot_novelty_trajectory`/`plot_diversity_trajectory`;
  a combined open-endedness-specific figure is a straightforward future
  addition, not a capability gap.
- **Potential vs. realized innovation** — `genevra.innovation.
  potential_vs_realized` computes the data; plotting it needs a paired
  time-series figure not yet built.

## CLI

```
genevra figures <result_path> --output-dir figures/
```

Writes whichever of figures 1-4 (plus the overview panel) the stored
trajectory supports.

## Formats

`save_figure(..., formats=("png",))` by default; pass
`formats=("png", "svg")` (or any matplotlib-supported format) for
additional outputs — matplotlib infers the writer from the file
extension, so no extra code is needed beyond the format list.
