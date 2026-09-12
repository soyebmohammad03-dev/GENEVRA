from __future__ import annotations

import json
from pathlib import Path

import pytest

from genevra.evidence.checksums import (
    sha256_file,
    verify_checksum_manifest,
    write_checksum_manifest,
)
from genevra.evidence.manifest import EvidenceArtifact, EvidenceManifest
from genevra.evidence.research_question import EvidenceStatus, ResearchQuestion
from genevra.evidence.robustness_classifier import RobustnessClassification, classify_robustness
from genevra.evidence.validation_split import split_seeds
from genevra.evidence.verify import verify_evidence_package


def _artifact(relative_path: str, research_question: str = "RQ1") -> EvidenceArtifact:
    return EvidenceArtifact(
        artifact_id=relative_path,
        artifact_type="figure",
        research_question=research_question,
        experiment_id="exp1",
        condition="a",
        seed_set=(0, 1),
        source_data="test",
        metric_ids=("fitness",),
        analysis_version="v1",
        config_hash="deadbeef",
        relative_path=relative_path,
    )


class TestChecksums:
    def test_write_and_verify_round_trip(self, tmp_path: Path) -> None:
        (tmp_path / "a.txt").write_text("hello")
        (tmp_path / "b.txt").write_text("world")
        manifest_path = tmp_path / "checksums" / "manifest.sha256"
        write_checksum_manifest(tmp_path, [tmp_path / "a.txt", tmp_path / "b.txt"], manifest_path)
        assert verify_checksum_manifest(tmp_path, manifest_path) == []

    def test_detects_corrupted_file(self, tmp_path: Path) -> None:
        target = tmp_path / "a.txt"
        target.write_text("hello")
        manifest_path = tmp_path / "checksums" / "manifest.sha256"
        write_checksum_manifest(tmp_path, [target], manifest_path)
        target.write_text("corrupted")
        mismatches = verify_checksum_manifest(tmp_path, manifest_path)
        assert len(mismatches) == 1
        assert mismatches[0].reason == "checksum mismatch"

    def test_detects_missing_file(self, tmp_path: Path) -> None:
        target = tmp_path / "a.txt"
        target.write_text("hello")
        manifest_path = tmp_path / "checksums" / "manifest.sha256"
        write_checksum_manifest(tmp_path, [target], manifest_path)
        target.unlink()
        mismatches = verify_checksum_manifest(tmp_path, manifest_path)
        assert mismatches[0].reason == "file missing"

    def test_sha256_file_deterministic(self, tmp_path: Path) -> None:
        target = tmp_path / "a.txt"
        target.write_text("hello")
        assert sha256_file(target) == sha256_file(target)


class TestManifest:
    def test_round_trip(self, tmp_path: Path) -> None:
        manifest = EvidenceManifest()
        manifest.add(_artifact("figures/fitness.png"))
        path = tmp_path / "manifest.json"
        manifest.save(path)
        loaded = EvidenceManifest.load(path)
        assert loaded.artifacts[0].relative_path == "figures/fitness.png"
        assert loaded.artifacts[0].seed_set == (0, 1)


class TestVerifyEvidencePackage:
    def _minimal_package(self, root: Path) -> None:
        for sub in ("figures", "tables", "reports", "checksums", "seeds"):
            (root / sub).mkdir(parents=True)
        (root / "figures" / "fitness.png").write_bytes(b"fake-png-bytes")
        manifest = EvidenceManifest()
        manifest.add(_artifact("figures/fitness.png"))
        manifest.save(root / "manifest.json")
        (root / "seeds" / "development_validation_split.json").write_text(
            json.dumps({"development_seeds": [0, 1], "validation_seeds": [2, 3]})
        )
        write_checksum_manifest(
            root,
            [p for p in root.rglob("*") if p.is_file()],
            root / "checksums" / "manifest.sha256",
        )

    def test_clean_package_verifies_ok(self, tmp_path: Path) -> None:
        self._minimal_package(tmp_path)
        report = verify_evidence_package(tmp_path)
        assert report.ok()

    def test_detects_orphaned_figure(self, tmp_path: Path) -> None:
        self._minimal_package(tmp_path)
        (tmp_path / "figures" / "orphan.png").write_bytes(b"not-in-manifest")
        # Corrupt neither checksum nor manifest — only add an untracked file.
        report = verify_evidence_package(tmp_path)
        assert not report.ok()
        assert "figures/orphan.png" in report.orphaned_files

    def test_detects_missing_referenced_file(self, tmp_path: Path) -> None:
        self._minimal_package(tmp_path)
        (tmp_path / "figures" / "fitness.png").unlink()
        report = verify_evidence_package(tmp_path)
        assert not report.ok()
        assert "figures/fitness.png" in report.missing_referenced_files

    def test_detects_seed_split_overlap(self, tmp_path: Path) -> None:
        self._minimal_package(tmp_path)
        (tmp_path / "seeds" / "development_validation_split.json").write_text(
            json.dumps({"development_seeds": [0, 1, 2], "validation_seeds": [2, 3]})
        )
        report = verify_evidence_package(tmp_path)
        assert not report.ok()
        assert report.seed_split_overlap == (2,)

    def test_missing_manifest_reported(self, tmp_path: Path) -> None:
        report = verify_evidence_package(tmp_path)
        assert not report.ok()
        assert "manifest.json" in report.missing_referenced_files


class TestValidationSplit:
    def test_no_overlap(self) -> None:
        split = split_seeds(list(range(10)), n_validation=3)
        assert not set(split.development_seeds) & set(split.validation_seeds)
        assert len(split.validation_seeds) == 3
        assert len(split.development_seeds) == 7

    def test_rejects_overlapping_construction(self) -> None:
        with pytest.raises(ValueError):
            from genevra.evidence.validation_split import SeedSplit

            SeedSplit(development_seeds=(0, 1, 2), validation_seeds=(2, 3))

    def test_rejects_out_of_range_n_validation(self) -> None:
        with pytest.raises(ValueError):
            split_seeds([0, 1, 2], n_validation=3)


class TestRobustnessClassifier:
    def test_insufficient_data_below_three_variants(self) -> None:
        report = classify_robustness("finding", {"a": 1.0, "b": -1.0})
        assert report.classification == RobustnessClassification.INSUFFICIENT_DATA

    def test_robust_when_all_signs_agree(self) -> None:
        report = classify_robustness("finding", {"a": 1.0, "b": 2.0, "c": 3.0, "d": 0.5})
        assert report.classification == RobustnessClassification.ROBUST
        assert report.agreement_fraction == 1.0

    def test_unstable_when_signs_split_exactly_evenly(self) -> None:
        report = classify_robustness("finding", {"a": 1.0, "b": -1.0, "c": 1.0, "d": -1.0})
        assert report.classification == RobustnessClassification.UNSTABLE
        assert report.agreement_fraction == 0.5

    def test_sensitive_when_majority_only_slightly_wins(self) -> None:
        variants = {chr(97 + i): (1.0 if i < 5 else -1.0) for i in range(8)}
        report = classify_robustness("finding", variants)
        assert report.agreement_fraction == pytest.approx(0.625)
        assert report.classification == RobustnessClassification.SENSITIVE


class TestResearchQuestion:
    def test_to_dict_serializes_status_value(self) -> None:
        rq = ResearchQuestion(
            question_id="RQ1",
            title="t",
            description="d",
            hypothesis_ids=("h1",),
            primary_outcome="fitness",
            secondary_outcomes=(),
            experimental_conditions=("a", "b"),
            required_replication=3,
            statistical_plan="permutation_test",
            evidence_status=EvidenceStatus.INCONCLUSIVE,
            limitations=("l1",),
        )
        assert rq.to_dict()["evidence_status"] == "INCONCLUSIVE"


class TestBuildEvidencePackage:
    def test_quick_scale_produces_verifiable_package(self, tmp_path: Path) -> None:
        from genevra.evidence.build import QUICK, build_evidence_package

        result = build_evidence_package(tmp_path / "evidence", QUICK)
        assert len(result.research_questions) == 9
        report = verify_evidence_package(tmp_path / "evidence")
        assert report.ok(), report.to_dict()

    def test_rq4_confounded_and_rq4b_corrected_both_present(self, tmp_path: Path) -> None:
        """RQ4 must stay CONFOUNDED regardless of significance thresholds
        (an audit finding about the experiment's design, not its data),
        and its same-engine correction RQ4b must be independently
        computed and traceable — closing the gap where RQ4b previously
        existed only in the committed package, not in `reproduce-evidence`
        itself."""
        from genevra.evidence.build import QUICK, build_evidence_package
        from genevra.evidence.research_question import EvidenceStatus

        result = build_evidence_package(tmp_path / "evidence", QUICK)
        by_id = {rq.question_id: rq for rq in result.research_questions}
        assert by_id["RQ4"].evidence_status == EvidenceStatus.CONFOUNDED
        assert by_id["RQ4b"].experiment_ids == ("exp_ecology_corrected",)
        assert by_id["RQ4b"].evidence_status in (
            EvidenceStatus.SUPPORTED,
            EvidenceStatus.PARTIALLY_SUPPORTED,
            EvidenceStatus.INCONCLUSIVE,
            EvidenceStatus.NOT_SUPPORTED,
            EvidenceStatus.CONTRADICTED,
            EvidenceStatus.INSUFFICIENT_DATA,
        )
        root = tmp_path / "evidence"
        assert (root / "statistics" / "rq4_corrected.json").exists()
        assert (root / "statistics" / "rq_family_fdr.json").exists()
        assert (root / "configurations" / "rq4_corrected_analysis_plan.json").exists()
        fdr = json.loads((root / "statistics" / "rq_family_fdr.json").read_text())
        hypothesis_ids = {r["hypothesis_id"] for r in fdr["records"]}
        assert "RQ4b_corrected_ecology" in hypothesis_ids
        # The CONFOUNDED original RQ4 is deliberately excluded from the FDR
        # family (correcting its p-value would misleadingly imply it is
        # still a candidate finding) — only its RQ4b_-prefixed correction
        # may appear.
        assert all(not h.startswith("RQ4_") for h in hypothesis_ids)

    def test_deterministic_case_a_metric_extraction(self, tmp_path: Path) -> None:
        from genevra.evidence.build import QUICK, build_evidence_package

        build_evidence_package(tmp_path / "run1", QUICK)
        build_evidence_package(tmp_path / "run2", QUICK)
        stats_path1 = tmp_path / "run1" / "statistics" / "case_a_reproduction.json"
        stats_path2 = tmp_path / "run2" / "statistics" / "case_a_reproduction.json"
        stats1 = json.loads(stats_path1.read_text())
        stats2 = json.loads(stats_path2.read_text())
        assert stats1["control_values"] == stats2["control_values"]
        assert stats1["treatment_values"] == stats2["treatment_values"]

    def test_no_research_question_left_not_tested_without_reason(self, tmp_path: Path) -> None:
        from genevra.evidence.build import QUICK, build_evidence_package

        result = build_evidence_package(tmp_path / "evidence", QUICK)
        for rq in result.research_questions:
            assert rq.limitations, f"{rq.question_id} has no documented limitations"
