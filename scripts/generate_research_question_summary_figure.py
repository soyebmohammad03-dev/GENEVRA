"""Regenerates `research_evidence/figures/research_question_summary.png`.

This is the one figure in `research_evidence/figures/` that is not produced
by `genevra.evidence.build.build_evidence_package` (which requires running
real evolution campaigns). It only reads already-committed structured
evidence — `research_evidence/tables/research_question_matrix.csv` — and
appends the resulting figure + its metadata sidecar to the existing
`research_evidence/manifest.json` and `research_evidence/checksums/manifest.sha256`,
without touching any other artifact. Safe to re-run any time the research
question matrix changes; it never invents a status or a number.

Usage: python scripts/generate_research_question_summary_figure.py
"""

from __future__ import annotations

import csv
from pathlib import Path

from genevra.artifacts.figures import plot_research_question_summary
from genevra.evidence.checksums import write_checksum_manifest
from genevra.evidence.manifest import EvidenceArtifact, EvidenceManifest

_ROOT = Path(__file__).resolve().parents[1] / "research_evidence"


def _config_hash(payload: dict[str, object]) -> str:
    import hashlib
    import json

    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()[:16]


def main() -> None:
    matrix_path = _ROOT / "tables" / "research_question_matrix.csv"
    with matrix_path.open(newline="") as f:
        rows = list(csv.DictReader(f))
    question_ids = tuple(sorted(r["question_id"] for r in rows))

    metadata = plot_research_question_summary(rows, output_dir=_ROOT / "figures")

    manifest_path = _ROOT / "manifest.json"
    manifest = EvidenceManifest.load(manifest_path)
    manifest.artifacts = [
        a for a in manifest.artifacts if not a.artifact_id.startswith("research_question_summary")
    ]
    config_hash = _config_hash({"question_ids": question_ids})
    for artifact_id, relative_path in (
        ("research_question_summary", "figures/research_question_summary.png"),
        ("research_question_summary_metadata", "figures/research_question_summary.json"),
    ):
        manifest.add(
            EvidenceArtifact(
                artifact_id=artifact_id,
                artifact_type="figure",
                research_question="ALL",
                experiment_id="ALL",
                condition="all",
                seed_set=(),
                source_data="research_evidence/tables/research_question_matrix.csv",
                metric_ids=("evidence_status",),
                analysis_version="artifacts.figures.v1",
                config_hash=config_hash,
                relative_path=relative_path,
                limitations=(metadata.limitations,),
                git_commit=metadata.git_commit,
            )
        )
    manifest.save(manifest_path)

    all_files = [p for p in _ROOT.rglob("*") if p.is_file() and p.name != "manifest.sha256"]
    write_checksum_manifest(_ROOT, all_files, _ROOT / "checksums" / "manifest.sha256")

    print(f"wrote figures/{metadata.files[0]} and figures/research_question_summary.json")
    print("updated manifest.json and checksums/manifest.sha256")


if __name__ == "__main__":
    main()
