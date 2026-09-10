"""Phase 10: GENEVRA's discovery engine — infrastructure for finding and
testing potentially interesting phenomena in stored experiment results,
never a claim of scientific discovery in its own right.

The pipeline this package implements: OBSERVE (`phenomena`, `anomaly`,
`correlation`) -> FORMULATE (`hypothesis`) -> propose a controlled TEST
(`followup`) -> optionally execute and evaluate (`loop`, `replication`) ->
record provenance (`memory`) and surface conflicts (`contradiction`) ->
summarize (`report`). Every stage produces evidence and uncertainty
information, never a verdict — see `docs/discovery_engine.md` and
`docs/hypothesis_protocol.md`.
"""
