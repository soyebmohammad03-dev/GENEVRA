"""Phase 11.2: a fully reproducible, serializable experiment design that
tests one `LiteratureClaim`.

`primary_metric`, `statistical_test`, `expected_direction`, and
`confidence_level` are locked in *before* any run happens (Phase 11.4's
anti-circularity requirement): `LiteratureReproductionRunner` never
chooses which metric "gives the desired result" after looking at the
data, it only ever evaluates whatever this spec already committed to.
The condition factories themselves (control/treatment `EvolutionConfig`
builders) are ordinary Python callables, exactly like every other
GENEVRA experiment in this repo (`experiments/*.py`,
`genevra.analysis.comparison.ComparisonRunner`) — they are not
serialized here, only referenced by name; a spec is reproducible given
its JSON plus the (checked-in, version-controlled) Python module that
defines its condition factories, the same reproducibility contract every
other experiment in this codebase already relies on.
"""

from __future__ import annotations

import dataclasses
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class LiteratureExperimentSpec:
    spec_id: str
    claim_id: str
    control_condition: str
    treatment_condition: str
    population_size: int
    generations: int
    seeds: tuple[int, ...]
    primary_metric: str
    """Dot/index path into the final trajectory generation's dict, e.g.
    `"genotypic_diversity"` or `"fitness_summary.mean"` or
    `"learning_gene_stats.1.mean"`. Locked before running."""
    statistical_test: str
    expected_direction: str
    confidence_level: float = 0.90
    replication_required_seeds: int = 4
    held_out_validation: bool = True
    approximation_notes: tuple[str, ...] = ()
    notes: str = ""

    def __post_init__(self) -> None:
        if len(self.seeds) < 2:
            raise ValueError("at least 2 seeds are required for a defined comparison")
        if len(set(self.seeds)) != len(self.seeds):
            raise ValueError("seeds must be unique")
        if self.population_size < 1:
            raise ValueError("population_size must be positive")
        if self.generations < 1:
            raise ValueError("generations must be positive")
        if self.expected_direction not in ("positive", "negative"):
            raise ValueError("expected_direction must be 'positive' or 'negative'")
        if not 0.0 < self.confidence_level < 1.0:
            raise ValueError("confidence_level must be in (0, 1)")
        if self.replication_required_seeds < 2:
            raise ValueError("replication_required_seeds must be >= 2")

    def to_dict(self) -> dict[str, Any]:
        return dataclasses.asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> LiteratureExperimentSpec:
        data = dict(data)
        data["seeds"] = tuple(data["seeds"])
        data["approximation_notes"] = tuple(data.get("approximation_notes", ()))
        return cls(**data)

    def save(self, path: Path) -> None:
        path.write_text(json.dumps(self.to_dict(), indent=2))

    @classmethod
    def load(cls, path: Path) -> LiteratureExperimentSpec:
        return cls.from_dict(json.loads(path.read_text()))


__all__ = ["LiteratureExperimentSpec"]
