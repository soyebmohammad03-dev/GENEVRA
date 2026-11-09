"""Create an ASCII JSS software attachment from the tracked distribution inputs."""

import argparse
import ast
import hashlib
import io
import json
import subprocess
import tokenize
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PUNCTUATION = str.maketrans(
    {"\u2014": "--", "\u2013": "-", "\u2018": "'", "\u2019": "'", "\u201c": '"', "\u201d": '"'}
)
README = """# GENEVRA JSS software source candidate

Install from this directory with Python 3.11 or later:
`python -m pip install .`. To install plotting support, use
`python -m pip install ".[viz]"`.

Run `genevra --help` and `genevra run --seed 0 --output baseline.json`.
Inspect the result with `genevra inspect baseline.json`.
See the attached help and the public reproduction guide for the frozen
publication workflow and its platform requirements.

The software uses the MIT license. Cite Soyeb Mohammad and the exact
GENEVRA revision and protocol described in CITATION.cff.
"""


def ascii_python(data: bytes, path: str) -> bytes:
    """Make comments readable and escape literals without changing the Python AST."""
    original = data.decode("utf-8")
    lines = original.splitlines(keepends=True)
    for token in tokenize.tokenize(io.BytesIO(data).readline):
        if token.type == tokenize.COMMENT and not token.string.isascii():
            row, start = token.start
            _, end = token.end
            line = lines[row - 1]
            lines[row - 1] = line[:start] + token.string.translate(PUNCTUATION) + line[end:]
    candidate = "".join(lines).encode("ascii", errors="backslashreplace")
    original_ast = ast.parse(original, filename=path, type_comments=True)
    candidate_ast = ast.parse(candidate, filename=path, type_comments=True)
    if ast.dump(original_ast) != ast.dump(candidate_ast):
        raise ValueError(f"ASCII conversion changed the parsed code: {path}")
    compile(candidate_ast, path, "exec")
    return candidate


def software_files() -> list[str]:
    """Select exactly the distributed package and source-build inputs."""
    tracked = subprocess.check_output(
        ["git", "ls-files", "-z", "--", "src/genevra"], cwd=ROOT
    ).decode()
    files = [path for path in tracked.split("\0") if path.endswith(".py")]
    config = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    forced = config["tool"]["hatch"]["build"]["targets"]["wheel"]["force-include"]
    return sorted([*files, *forced, "README.md", "LICENSE", "CITATION.cff", "pyproject.toml"])


def prepare(output: Path) -> None:
    """Assemble a new tree and write a machine-readable source inventory."""
    contents = {}
    inventory = []
    for name in software_files():
        original = (ROOT / name).read_bytes()
        if name.endswith(".py"):
            candidate = ascii_python(original, name)
        elif name == "README.md":
            candidate = README.encode("ascii")
        else:
            candidate = original
        if not candidate.isascii():
            raise ValueError(f"non-ASCII candidate file: {name}")
        contents[name] = candidate
        inventory.append(
            {
                "path": name,
                "original_sha256": hashlib.sha256(original).hexdigest(),
                "candidate_sha256": hashlib.sha256(candidate).hexdigest(),
                "disposition": (
                    "submission readme"
                    if name == "README.md"
                    else "AST verified"
                    if name.endswith(".py")
                    else "verbatim"
                ),
            }
        )
    output.mkdir()
    for name, candidate in contents.items():
        path = output / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(candidate)
    (output / "source-inventory.json").write_text(
        json.dumps(inventory, indent=2) + "\n", encoding="ascii"
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    prepare(args.output)
