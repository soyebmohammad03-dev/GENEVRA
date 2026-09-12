"""Phase 16: population-level scaling of Phase 13's mechanism analyses.

Phase 13's `genevra.mechanisms` analyzers operate on one genome at a
time. This package adds an aggregation layer *on top* of them — it does
not re-implement or replace their math. The independent seed/run is the
unit of replication for every cross-condition statistical claim here;
values from different organisms within one run are never treated as
independent observations. See `docs/population_analysis.md`.
"""

from __future__ import annotations
