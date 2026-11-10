"""Phase 19.14: SHA-256 checksums for curated evidence artifacts.

Format matches the standard `sha256sum` tool's output
(`<hex digest>  <path relative to root>`) so `sha256sum -c` also works
against the checked-in manifest, not only `verify_checksum_manifest`.
"""

from __future__ import annotations

import hashlib
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path, PureWindowsPath


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


def resolve_evidence_path(root: Path, name: str) -> Path:
    """Resolve a relative package path while keeping its target under root."""
    relative = Path(name)
    if (
        not relative.parts
        or relative.is_absolute()
        or PureWindowsPath(name).drive
        or "\\" in name
        or ".." in relative.parts
    ):
        raise ValueError("unsafe evidence path")
    try:
        canonical_root = root.resolve()
        resolved = (canonical_root / relative).resolve()
    except (OSError, RuntimeError, ValueError) as exc:
        raise ValueError("unsafe evidence path") from exc
    if not resolved.is_relative_to(canonical_root):
        raise ValueError("unsafe evidence path")
    return resolved


def verify_checksum_manifest(root: Path, manifest_path: Path) -> list[ChecksumMismatch]:
    """Returns every mismatch found — an empty list means every file the
    manifest lists exists at the recorded root and still hashes to the
    recorded digest. Does not detect extra, unlisted files (that is
    `genevra.evidence.verify`'s orphan-detection job, not this one)."""
    try:
        manifest_name = manifest_path.absolute().relative_to(root.absolute()).as_posix()
        manifest = resolve_evidence_path(root, manifest_name)
    except ValueError:
        return [ChecksumMismatch(str(manifest_path), "unsafe evidence path")]
    if not manifest.is_file():
        return [ChecksumMismatch(str(manifest_path), "manifest file does not exist")]
    mismatches: list[ChecksumMismatch] = []
    for line in manifest.read_text().splitlines():
        if not line.strip():
            continue
        expected_digest, _, rel_path = line.partition("  ")
        try:
            target = resolve_evidence_path(root, rel_path)
        except ValueError:
            mismatches.append(ChecksumMismatch(rel_path, "unsafe evidence path"))
            continue
        if not target.is_file():
            mismatches.append(ChecksumMismatch(rel_path, "file missing"))
            continue
        actual_digest = sha256_file(target)
        if actual_digest != expected_digest:
            mismatches.append(ChecksumMismatch(rel_path, "checksum mismatch"))
    return mismatches


__all__ = ["sha256_file", "write_checksum_manifest", "ChecksumMismatch", "verify_checksum_manifest"]
