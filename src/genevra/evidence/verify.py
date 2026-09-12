"""Phase 19.16: `verify-evidence` logic.

Checks the four things a curated evidence package can silently get
wrong: a checksum that no longer matches the file on disk, a manifest
entry pointing at a path that does not exist, a file under a
manifest-tracked directory that no manifest entry references (orphan),
and development/validation seed sets that have started overlapping.
Every check reports concrete findings; there is no single boolean
"looks fine."
"""

from __future__ import annotations

import dataclasses
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from genevra.evidence.checksums import ChecksumMismatch, verify_checksum_manifest
from genevra.evidence.manifest import EvidenceManifest

_MANIFEST_TRACKED_DIRS = ("figures", "tables", "reports")


@dataclass(frozen=True)
class EvidenceVerificationReport:
    checksum_mismatches: tuple[ChecksumMismatch, ...]
    missing_referenced_files: tuple[str, ...]
    orphaned_files: tuple[str, ...]
    seed_split_overlap: tuple[int, ...]

    def ok(self) -> bool:
        return not (
            self.checksum_mismatches
            or self.missing_referenced_files
            or self.orphaned_files
            or self.seed_split_overlap
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok(),
            "checksum_mismatches": [dataclasses.asdict(m) for m in self.checksum_mismatches],
            "missing_referenced_files": list(self.missing_referenced_files),
            "orphaned_files": list(self.orphaned_files),
            "seed_split_overlap": list(self.seed_split_overlap),
        }


def verify_evidence_package(root: Path) -> EvidenceVerificationReport:
    manifest_path = root / "manifest.json"
    checksum_path = root / "checksums" / "manifest.sha256"

    checksum_mismatches = tuple(verify_checksum_manifest(root, checksum_path))

    missing: list[str] = []
    referenced: set[str] = set()
    if manifest_path.exists():
        manifest = EvidenceManifest.load(manifest_path)
        for artifact in manifest.artifacts:
            referenced.add(artifact.relative_path)
            if not (root / artifact.relative_path).exists():
                missing.append(artifact.relative_path)
    else:
        missing.append(str(manifest_path.relative_to(root)))

    orphaned: list[str] = []
    for tracked in _MANIFEST_TRACKED_DIRS:
        tracked_dir = root / tracked
        if not tracked_dir.exists():
            continue
        for path in tracked_dir.rglob("*"):
            if path.is_file():
                rel = path.relative_to(root).as_posix()
                if rel not in referenced:
                    orphaned.append(rel)

    seed_overlap: tuple[int, ...] = ()
    seeds_path = root / "seeds" / "development_validation_split.json"
    if seeds_path.exists():
        split = json.loads(seeds_path.read_text())
        dev = set(split.get("development_seeds", []))
        val = set(split.get("validation_seeds", []))
        seed_overlap = tuple(sorted(dev & val))

    return EvidenceVerificationReport(
        checksum_mismatches=checksum_mismatches,
        missing_referenced_files=tuple(missing),
        orphaned_files=tuple(orphaned),
        seed_split_overlap=seed_overlap,
    )


__all__ = ["EvidenceVerificationReport", "verify_evidence_package"]
