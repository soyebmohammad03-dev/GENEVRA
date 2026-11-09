"""Verify wheel contents, installed CLI help, and dependency license metadata."""

import argparse
import hashlib
import importlib.metadata
import json
import subprocess
import sys
from pathlib import Path
from zipfile import ZipFile

from genevra.cli import build_parser
from genevra.utils.provenance import source_commit

SCRIPTS = ("baseline.py", "exp1_isolated_vs_shared.py", "exp_ecology_corrected.py")


def audit(wheel: Path, root: Path, output: Path) -> None:
    """Write a machine-readable receipt for the wheel and current install."""
    with ZipFile(wheel) as archive:
        files = archive.namelist()
        if len(set(files)) != len(files) or any(
            not (
                name.startswith("genevra/")
                and name.endswith(".py")
                or name.startswith("genevra-")
                and ".dist-info/" in name
            )
            for name in files
        ):
            raise ValueError("unexpected or duplicate wheel members")
        if not any(name.endswith(".dist-info/licenses/LICENSE") for name in files):
            raise ValueError("missing project license")
        prefix = "genevra/experiments/_scripts/"
        if {name.removeprefix(prefix) for name in files if name.startswith(prefix)} != set(SCRIPTS):
            raise ValueError("runtime script inventory differs")
        for name in SCRIPTS:
            if archive.read(prefix + name) != (root / "experiments" / name).read_bytes():
                raise ValueError(f"bundled experiment differs from checkout: {name}")
        sources = {name: archive.read(name) for name in files if name.endswith(".py")}
        for data in sources.values():
            data.decode("utf-8")
        non_ascii = sorted(name for name, data in sources.items() if not data.isascii())
        cr = sorted(name for name, data in sources.items() if b"\r" in data)
        if cr:
            raise ValueError(f"unexpected CR line endings: {cr}")
    if source_commit() is not None:
        raise ValueError("wheel incorrectly attributed itself to a Git checkout")
    parser = build_parser()
    subparsers = next(a for a in parser._actions if isinstance(a, argparse._SubParsersAction))
    help_dir = output.parent / "help"
    help_dir.mkdir()
    for command in ("", *subparsers.choices):
        args = [sys.executable, "-I", "-m", "genevra.cli"]
        rendered = subprocess.check_output([*args, *command.split(), "--help"], text=True)
        (help_dir / f"{command or 'genevra'}.txt").write_text(rendered, encoding="utf-8")
    inventory = []
    for dist in importlib.metadata.distributions():
        metadata = dist.metadata
        inventory.append(
            {
                "name": metadata["Name"],
                "version": dist.version,
                "license_expression": metadata.get("License-Expression"),
                "license_classifiers": [
                    label
                    for label in metadata.get_all("Classifier", [])
                    if label.startswith("License")
                ],
                "license_files": metadata.get_all("License-File", []),
            }
        )
    receipt = {
        "wheel": wheel.name,
        "sha256": hashlib.sha256(wheel.read_bytes()).hexdigest(),
        "runtime_scripts": SCRIPTS,
        "python_file_count": len(sources),
        "non_ascii_sources": non_ascii,
        "packages": sorted(inventory, key=lambda row: row["name"].lower()),
        "help_commands": list(subparsers.choices),
    }
    with output.open("x", encoding="utf-8") as f:
        json.dump(receipt, f, indent=2)
        f.write("\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("wheel", type=Path)
    parser.add_argument("checkout", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    audit(args.wheel, args.checkout, args.output)
