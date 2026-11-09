"""Locate the source of this GENEVRA installation for provenance."""

import subprocess
from pathlib import Path


def source_checkout() -> Path | None:
    """Return the source checkout containing this package, when present."""
    package = Path(__file__).resolve().parent.parent
    root = package.parent.parent
    if package.parent.name == "src" and (root / "pyproject.toml").is_file():
        return root
    return None


def source_commit() -> str | None:
    """Return the checkout revision, or None when this is a standalone install."""
    root = source_checkout()
    if root is None or not (root / ".git").exists():
        return None
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=root,
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    return result.stdout.strip() if result.returncode == 0 else None
