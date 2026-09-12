"""Phase 11.8: a literature reproduction registry — implemented as
records inside the existing `genevra.discovery.memory.ResearchMemory`,
not a second, disconnected provenance store. A claim becomes a
`"literature_claim"` record; each reproduction attempt becomes a
`"reproduction_result"` record whose `parent_ids` point back at the claim
it tested, so `ResearchMemory.trace_lineage`/`children` walk the same
claim -> spec -> result chain as every other GENEVRA provenance record.
"""

from __future__ import annotations

import hashlib
import json

from genevra.discovery.memory import ResearchMemory, ResearchRecord
from genevra.literature.claims import LiteratureClaim
from genevra.literature.runner import ReproductionResult
from genevra.literature.spec import LiteratureExperimentSpec


def config_hash(spec: LiteratureExperimentSpec) -> str:
    """A short, deterministic hash of the spec's own configuration
    (everything needed to reproduce the run: conditions, seeds,
    population size, generations, primary metric, statistical test) —
    not of the source code, which git commit hashes already track."""
    payload = json.dumps(spec.to_dict(), sort_keys=True).encode()
    return hashlib.sha256(payload).hexdigest()[:16]


def register_claim(memory: ResearchMemory, claim: LiteratureClaim) -> str:
    """Idempotent: re-registering the same `claim_id` is a no-op rather
    than an error, since a case module may be re-imported across a
    session and register the same claim more than once."""
    record_id = f"literature_claim::{claim.claim_id}"
    if record_id not in memory.records:
        memory.add(
            ResearchRecord(
                record_id=record_id, record_type="literature_claim", payload=claim.to_dict()
            )
        )
    return record_id


def register_reproduction(
    memory: ResearchMemory,
    spec: LiteratureExperimentSpec,
    result: ReproductionResult,
    claim_record_id: str,
    genevra_version: str,
) -> str:
    record_id = f"reproduction_result::{spec.spec_id}"
    payload = {
        "spec": spec.to_dict(),
        "config_hash": config_hash(spec),
        "genevra_version": genevra_version,
        "seeds": list(spec.seeds),
        "label": result.label.value,
        "n_control": result.n_control,
        "n_treatment": result.n_treatment,
        "observed_direction": result.observed_direction,
        "expected_direction": result.expected_direction,
        "effect_size_cohens_d": (
            result.effect_size.cohens_d if result.effect_size is not None else None
        ),
        "p_value": result.permutation.p_value if result.permutation is not None else None,
        "validation_errors": list(result.validation.errors),
        "validation_warnings": list(result.validation.warnings),
    }
    if record_id in memory.records:
        raise ValueError(f"reproduction result {record_id!r} already registered")
    memory.add(
        ResearchRecord(
            record_id=record_id,
            record_type="reproduction_result",
            payload=payload,
            parent_ids=(claim_record_id,),
        )
    )
    return record_id


__all__ = ["config_hash", "register_claim", "register_reproduction"]
