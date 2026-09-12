"""Phase 19.14: SHA-256 checksums for curated evidence artifacts.

Format matches the standard `sha256sum` tool's output
(`<hex digest>  <path relative to root>`) so `sha256sum -c` also works
against the checked-in manifest, not only `verify_checksum_manifest`.
"""

from __future__ import annotations

import hashlib
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    digest.update(path.read_bytes())
    return digest.hexdigest()


def write_checksum_manifest(root: Path, files: Iterable[Path], manifest_path: Path) -> None:
    lines = []
    for file_path in sorted(files):
        rel = file_path.relative_to(root)
        lines.append(f"{sha256_file(file_path)}  {rel.as_posix()}")
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text("\n".join(lines) + ("\n" if lines else ""))


@dataclass(frozen=True)
class ChecksumMismatch:
    path: str
    reason: str


def verify_checksum_manifest(root: Path, manifest_path: Path) -> list[ChecksumMismatch]:
    """Returns every mismatch found — an empty list means every file the
    manifest lists exists at the recorded root and still hashes to the
    recorded digest. Does not detect extra, unlisted files (that is
    `genevra.evidence.verify`'s orphan-detection job, not this one)."""
    if not manifest_path.exists():
        return [ChecksumMismatch(str(manifest_path), "manifest file does not exist")]
    mismatches: list[ChecksumMismatch] = []
    for line in manifest_path.read_text().splitlines():
        if not line.strip():
            continue
        expected_digest, _, rel_path = line.partition("  ")
        target = root / rel_path
        if not target.exists():
            mismatches.append(ChecksumMismatch(rel_path, "file missing"))
            continue
        actual_digest = sha256_file(target)
        if actual_digest != expected_digest:
            mismatches.append(ChecksumMismatch(rel_path, "checksum mismatch"))
    return mismatches


__all__ = ["sha256_file", "write_checksum_manifest", "ChecksumMismatch", "verify_checksum_manifest"]
