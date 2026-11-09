from pathlib import Path

import pytest

from genevra.experiments import _resources
from genevra.utils import provenance


def test_loader_rejects_non_runtime_script() -> None:
    with pytest.raises(ValueError, match="unknown runtime experiment"):
        _resources.load_experiment_script("../baseline.py")


def test_missing_resource_reports_reinstall(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(_resources.resources, "files", lambda _: tmp_path)
    monkeypatch.setattr(_resources, "source_checkout", lambda: None)
    with pytest.raises(RuntimeError, match="missing GENEVRA runtime resource.*reinstall"):
        _resources.load_experiment_script("baseline.py")


def test_revision_ignores_caller_checkout(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(provenance, "source_checkout", lambda: None)
    assert provenance.source_commit() is None
