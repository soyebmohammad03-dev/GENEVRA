"""Post-hoc analysis over experiment results.

Everything here consumes `ExperimentResult`/`ExperimentResult.to_dict()`
data (or `EcologicalSnapshot` sequences for the continuous engine) — plain
dicts and dataclasses already produced by `genevra.experiments` and
`genevra.evolution`. Nothing in this package reaches back into a live
simulator, environment, or organism: analysis operates on recorded
results, never on hidden state, so a result computed once can always be
re-analyzed later without re-running anything.

A single run is not a scientific result. This package's job is to make it
possible to run several (seeds x conditions), aggregate them honestly
(including when some fail or end early — see `aggregation.py`), and look
for the signals GENEVRA's research questions actually turn on: whether
diversity/novelty/evolvability decline together in a way that looks like
stagnation (`stagnation.py`, which explicitly does not equate a fitness
plateau with stagnation), how lineages branch and persist
(`lineage_analysis.py`), and whether evolvability itself changes over
evolutionary time (`evolvability_over_time.py`).
"""
