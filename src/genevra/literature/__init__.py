"""Phase 11: literature reproduction and falsification lab.

Encodes published evolutionary claims as explicit, falsifiable
`LiteratureClaim`/`LiteratureExperimentSpec` pairs, tests whether they
survive under GENEVRA's own model assumptions via
`LiteratureReproductionRunner`, and generates alternative explanations and
falsification experiments rather than accepting a first significant result
at face value. Nothing here claims to reproduce a paper's experiment
exactly, and no scientific conclusion is hard-coded — every result is a
computed label (see `genevra.literature.runner.ReproductionLabel`)
attached to the evidence that produced it.
"""

from __future__ import annotations
