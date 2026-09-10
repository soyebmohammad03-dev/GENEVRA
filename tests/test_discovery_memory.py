import json
from pathlib import Path

import pytest

from genevra.discovery.memory import ResearchMemory, ResearchRecord


def _memory() -> ResearchMemory:
    memory = ResearchMemory()
    memory.add(ResearchRecord("obs1", "phenomenon", {"name": "novelty_without_fitness_gain"}))
    memory.add(ResearchRecord("hyp1", "hypothesis", {"statement": "x"}, parent_ids=("obs1",)))
    memory.add(
        ResearchRecord("exp1", "experiment_result", {"status": "completed"}, parent_ids=("hyp1",))
    )
    memory.add(ResearchRecord("followup1", "followup", {"note": "n"}, parent_ids=("exp1",)))
    return memory


def test_children_returns_direct_descendants() -> None:
    memory = _memory()
    children = memory.children("obs1")
    assert [c.record_id for c in children] == ["hyp1"]


def test_trace_lineage_walks_back_to_the_root() -> None:
    memory = _memory()
    chain = memory.trace_lineage("followup1")
    assert [r.record_id for r in chain] == ["obs1", "hyp1", "exp1", "followup1"]


def test_duplicate_record_id_raises() -> None:
    memory = _memory()
    with pytest.raises(ValueError):
        memory.add(ResearchRecord("obs1", "phenomenon", {}))


def test_by_type_filters_records() -> None:
    memory = _memory()
    assert [r.record_id for r in memory.by_type("hypothesis")] == ["hyp1"]


def test_save_and_load_round_trip(tmp_path: Path) -> None:
    memory = _memory()
    path = tmp_path / "memory.json"
    memory.save(path)
    loaded = ResearchMemory.load(path)
    assert set(loaded.records.keys()) == set(memory.records.keys())
    assert loaded.get("hyp1").parent_ids == ("obs1",)
    assert json.loads(path.read_text())[0]["record_id"] in memory.records
