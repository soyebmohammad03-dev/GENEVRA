# Research campaigns (Phase 17)

A `ResearchCampaign` runs `condition x replicate` cells, checkpointed and
resumable, with every individual run preserved (not just an aggregate) and
bundled into `research_artifacts/campaigns/<campaign_id>/` with complete
provenance. This is the fix for the Phase 15/16 traceability gap: ecology
and population-analysis results now have a path into the same artifact
system as everything else in `genevra.artifacts`.

## Seed hierarchy

```
campaign_seed
    -> condition_seed   (genevra.campaign.seeding.derive_condition_seeds)
        -> replicate_seed  (derive_replicate_seeds)
```

Built on `numpy.random.SeedSequence.spawn`, not a hand-rolled hash: calling
`derive_condition_seeds(seed, n)` twice always returns the same `n` seeds,
and it is *prefix-stable* — `derive_condition_seeds(seed, 5)[:2] ==
derive_condition_seeds(seed, 2)`, so adding a condition to a campaign
config does not change any earlier condition's stream. `derive_run_seed`
recomputes one specific cell's seed from its two indices alone (used to
verify a checkpointed run's recorded seed without re-deriving every seed
in the campaign).

## Checkpointing and resume

`CampaignRunner` writes `runs/checkpoint.json` and one JSON file per
completed cell under `runs/<condition_id>/<replicate_index>.json`.
Constructing a new `CampaignRunner` against the same `runs_dir` — as a
fresh process would after an interruption — reloads that checkpoint:

- `COMPLETED`/`FAILED` cells are skipped (not re-executed, not silently
  overwritten).
- Any cell left `RUNNING` (the process died mid-run) is reclassified
  `INTERRUPTED` on load and is treated as pending — it *is* redone, since
  its result was never actually written.

`genevra campaign-resume` is the same code path as `genevra campaign`
pointed at the same `--output-root`/`--campaign-id`; there is no separate
resume mechanism to keep in sync with the main one.

## Traceability

`generate_campaign_bundle` writes, under
`research_artifacts/campaigns/<campaign_id>/`:

- `manifest.json` — the full `CampaignConfig`, its `config_hash`, and the
  git commit that produced it.
- `analysis_plan.json` — the frozen `AnalysisPlan` (Phase 17.8), written
  before execution and only ever read back, never regenerated after
  looking at results.
- `conditions/<id>.json` — requested/completed/failed seeds per condition.
- `runs/` — the checkpoint plus every individual cell's raw result.
- `quality_gate.json` — `genevra.innovation.quality_gates.evaluate_quality_gates`
  applied to this campaign's facts (reused, not reimplemented).
- the standard `provenance/`, `configurations/`, `seeds/`, `reports/`
  (and unused-but-present `raw_data/`, `derived_data/`, `metrics/`,
  `figures/`, `tables/`, `logs/`, `supplementary/`) from
  `genevra.artifacts.directory.ArtifactDirectory`.

Every figure/table/report a campaign produces is written under this same
tree, so nothing is orphaned outside it.

## Multiple comparisons and confirmatory/exploratory separation

`genevra.campaign.multiple_comparison.build_multiple_comparison_registry`
wraps the existing `genevra.discovery.multiple_testing.benjamini_hochberg`
— every hypothesis/metric examined in a campaign is corrected together as
one family, and each result is labeled `confirmatory` (its `is_primary`
flag was set, i.e. it was in the frozen analysis plan) or `exploratory`
(noticed afterward). `CampaignReport` never presents an exploratory
finding as confirmation.

## Known limitation

The `genevra campaign` CLI command demonstrates the architecture on a tiny
isolated-vs-shared-ecology comparison (a single scalar metric per run, 3-4
replicates) — a laptop smoke test proving the pipeline works end to end,
not a research-scale finding. Running `CampaignConfig` at `STANDARD`/
`RESEARCH` mode sizes (see `genevra.population_analysis.matrix` for the
existing size conventions this reuses) is left to a future, purpose-built
campaign, not built or executed here.
