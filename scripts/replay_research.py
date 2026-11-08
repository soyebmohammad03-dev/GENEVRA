"""Verify and replay archived GENEVRA studies in a fresh directory."""

import argparse
import hashlib
import json
import os
import subprocess
import sys
import time
import urllib.request
from pathlib import Path, PurePosixPath
from zipfile import ZipFile

PHASES = tuple(map(str, range(11, 20))) + ("19-extension",)
CATALOG = Path(__file__).resolve().parents[1] / "docs/research/archive.json"


def sha(path: Path) -> str:
    with path.open("rb") as handle:
        return hashlib.file_digest(handle, "sha256").hexdigest()


def extract(archive: Path, destination: Path, expected: str) -> None:
    """Check the outer archive and every member before publishing extracted data."""
    if sha(archive) != expected:
        raise ValueError("archive SHA-256 mismatch")
    with ZipFile(archive) as zipped:
        members = zipped.namelist()
        if len(members) != len(set(members)):
            raise ValueError("duplicate member")
        for name in members:
            path = PurePosixPath(name)
            if path.is_absolute() or ".." in path.parts or "\\" in name:
                raise ValueError(f"unsafe archive member: {name}")
        checks = [line.split("  ", 1) for line in zipped.read("SHA256SUMS").decode().splitlines()]
        if len(checks) != len(members) - 1 or {name for _, name in checks} != set(members) - {
            "SHA256SUMS"
        }:
            raise ValueError("archive manifest does not cover exactly the payload")
        for digest, name in checks:
            if hashlib.sha256(zipped.read(name)).hexdigest() != digest:
                raise ValueError(f"member SHA-256 mismatch: {name}")
        # ZipFile extracts regular files and does not restore symlinks.
        zipped.extractall(destination)


def replay(phase: str, root: Path, output: Path, env: dict[str, str]) -> None:
    source = root / f"phase-{phase}"
    command: list[str | Path]
    expected: Path | None = None
    if phase in (*PHASES[:6], "18"):
        command = ["sh", "reproduce.sh", output]
    elif phase == "17":
        command = [
            sys.executable,
            "reconstruct.py",
            root / "phase-15/results",
            root / "phase-16/results",
            output,
        ]
    elif phase == "19":
        output.mkdir()
        command = [
            sys.executable,
            "docs/verify_phase18.py",
            root / "phase-18",
            output / "reconstruction.json",
        ]
        expected = source / "docs/reconstruction.json"
    else:
        output.mkdir()
        protocol = Path("docs/model_repair/phase_19/extension")
        command = [
            sys.executable,
            "experiments/coverage_envelope_study.py",
            "analyze",
            protocol,
            "raw.json",
            output / "results.json",
        ]
        expected = source / protocol / "results.json"
    phase_env = {**env, "PYTHONPATH": str(source / "src")}
    subprocess.run(command, cwd=source, env=phase_env, check=True)
    if expected is not None and sha(expected) != sha(output / expected.name):
        raise ValueError(f"Phase {phase} reconstruction differs from archived output")
    if phase == "17":
        for name in ("baseline.csv", "paired_coverage.csv"):
            if sha(source / "derived" / name) != sha(output / name):
                raise ValueError(f"Phase 17 comparison differs: {name}")
    if phase == "19-extension":
        subprocess.run(
            [
                sys.executable,
                protocol / "verify.py",
                protocol / "config.json",
                "raw.json",
                output / "results.json",
            ],
            cwd=source,
            env=phase_env,
            check=True,
        )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path, help="use an already downloaded release asset")
    parser.add_argument("--phase", action="append", choices=PHASES, help="default is all phases")
    parser.add_argument("--output", type=Path, required=True, help="must be a new directory")
    args = parser.parse_args()
    config = json.loads(CATALOG.read_text())
    destination = args.output.resolve()
    destination.mkdir()
    archive = args.archive
    if archive is None:
        archive = destination / config["asset"]
        with urllib.request.urlopen(config["url"], timeout=90) as response, archive.open("xb") as f:
            while block := response.read(1024 * 1024):
                f.write(block)
    root = destination / "archive"
    extract(archive, root, config["sha256"])
    env = {
        **os.environ,
        "PYTHON": sys.executable,
        "MPLBACKEND": "Agg",
        "OPENBLAS_NUM_THREADS": "1",
        "VECLIB_MAXIMUM_THREADS": "1",
        "OMP_NUM_THREADS": "1",
    }
    elapsed = {}
    for phase in dict.fromkeys(args.phase or PHASES):
        start = time.monotonic()
        replay(phase, root, destination / f"phase-{phase}", env)
        elapsed[phase] = round(time.monotonic() - start, 3)
        print(f"Phase {phase} verified in {elapsed[phase]:.3f}s", flush=True)
    receipt = {"archive_sha256": config["sha256"], "python": sys.version, "elapsed_s": elapsed}
    (destination / "receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")


if __name__ == "__main__":
    main()
