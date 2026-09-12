"""Phase 11.1: a structured representation of a literature-derived
scientific claim.

A `LiteratureClaim` is a hypothesis/expectation an experiment can support,
fail to support, or leave unresolved — never a conclusion this module
asserts on its own. No scientific finding from the source paper is
hard-coded into GENEVRA's engine anywhere; this dataclass only records the
paper's claim in a form an experiment spec can be checked against.
"""

from __future__ import annotations

import dataclasses
from dataclasses import dataclass
from typing import Any, Literal

ExpectedDirection = Literal["positive", "negative", "none", "unspecified"]


@dataclass(frozen=True)
class LiteratureClaim:
    claim_id: str
    source_reference: str
    source_year: int
    research_question: str
    claim_text: str
    independent_variable: str
    dependent_variable: str
    environmental_regime: str
    organism_assumptions: str
    evolutionary_assumptions: str
    measurement_definition: str
    expected_direction: ExpectedDirection
    expected_relationship: str
    known_limitations: tuple[str, ...]
    genevra_mapping: str
    """How this claim's variables map onto GENEVRA's own model. Must state
    explicitly, in prose, where the mapping is an approximation rather
    than a faithful reproduction of the source paper's model — see each
    entry in `genevra.literature.cases` for examples."""
    replication_status: str = "not_attempted"
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        return dataclasses.asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> LiteratureClaim:
        data = dict(data)
        data["known_limitations"] = tuple(data.get("known_limitations", ()))
        return cls(**data)


__all__ = ["LiteratureClaim", "ExpectedDirection"]
