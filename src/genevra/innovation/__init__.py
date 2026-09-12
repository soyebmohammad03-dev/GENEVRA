"""Phase 12: open-endedness and innovation dynamics lab.

Upgrades GENEVRA's open-endedness analysis from a small proxy suite
(`genevra.analysis.open_endedness`) into a multi-dimensional diagnostic
framework, inspired by (but not a copy of) the MODES framework (Dolson et
al. 2019): explicit `InnovationEvent` detection kept separate from raw
fitness change, lineage-based (not merely temporal) innovation-dependency
inference, evolutionary activity built on GENEVRA's own lineage/strategy
machinery, potential-vs-realized innovation, trajectory/phase-space
analysis, and configurable research-quality gates. No module here ever
emits a single "OPEN_ENDED = True/False" verdict.
"""

from __future__ import annotations
