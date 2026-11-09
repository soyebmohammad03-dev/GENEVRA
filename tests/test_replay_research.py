"""Integrity checks for the public archived replay boundary."""

import hashlib
import runpy
from pathlib import Path
from zipfile import ZipFile

import pytest

ROOT = Path(__file__).resolve().parents[1]
REPLAY = runpy.run_path(str(ROOT / "scripts/replay_research.py"))


@pytest.mark.parametrize("problem", [None, "archive", "member", "traversal", "unlisted"])
def test_archive_verification(tmp_path, problem):
    archive = tmp_path / "data.zip"
    destination = tmp_path / "output"
    name = "../escape" if problem == "traversal" else "phase-11/config.json"
    data = b"fixed input"
    digest = hashlib.sha256(data).hexdigest()
    with ZipFile(archive, "w") as zipped:
        zipped.writestr(name, b"altered input" if problem == "member" else data)
        if problem == "unlisted":
            zipped.writestr("unlisted.json", b"{}")
        zipped.writestr("SHA256SUMS", f"{digest}  {name}\n")
    expected = "0" * 64 if problem == "archive" else REPLAY["sha"](archive)
    if problem:
        with pytest.raises(ValueError):
            REPLAY["extract"](archive, destination, expected)
        assert not destination.exists()
    else:
        REPLAY["extract"](archive, destination, expected)
        assert (destination / name).read_bytes() == data
