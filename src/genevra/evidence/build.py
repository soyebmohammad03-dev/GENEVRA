"""Phase 19.23/19.30: executes the final evidence campaigns for real and
writes a curated `research_evidence/` package from their actual output.

Every number this module writes comes from one of the real runs it
executes here — `ComparisonRunner`, `CampaignRunner`,
`RobustnessAnalyzer`/`EvolvabilityAnalyzer`, `run_boundary_sweep`,
`PhenomenonDetector` — never a hand-entered value. `scale="quick"` runs a
much smaller version of the same pipeline (for tests and the
`reproduce-evidence` CLI's fast default); `scale="full"` is what
generated the checked-in `research_evidence/` package. The two scales
share every line of analysis code; only sample sizes differ, and the
actual sizes used are always recorded in the output, never assumed.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np

from genevra.analysis.aggregation import (
    EffectSizeResult,
    PermutationTestResult,
    cohens_d,
    permutation_test,
)
from genevra.analysis.comparison import ComparisonRunner, ComparisonValidation, validate_comparison
from genevra.artifacts.figures import (
    plot_diversity_trajectory,
    plot_fitness_trajectory,
    plot_novelty_trajectory,
    plot_robustness_vs_evolvability,
)
from genevra.artifacts.tables import to_csv, to_markdown
from genevra.discovery.followup import generate_followup_experiment
from genevra.discovery.hypothesis import hypotheses_from_recurring_phenomena
from genevra.discovery.phenomena import PhenomenonDetector
from genevra.evidence.checksums import write_checksum_manifest
from genevra.evidence.manifest import EvidenceArtifact, EvidenceManifest
from genevra.evidence.metric_registry import REGISTRY
from genevra.evidence.research_question import EvidenceStatus, ResearchQuestion
from genevra.evidence.robustness_classifier import classify_robustness
from genevra.evidence.validation_split import split_seeds
from genevra.evolution.lifetime import run_single_lifetime
from genevra.literature.boundary_search import run_boundary_sweep
from genevra.literature.cases import case_a_plasticity_evolvability_tradeoff
from genevra.literature.comparison_matrix import (
    ComparisonRow,
    comparison_matrix_csv,
    comparison_matrix_markdown,
)
from genevra.literature.runner import (
    ReproductionLabel,
    ReproductionResult,
    classify_evidence,
    extract_metric,
)
from genevra.literature.spec import LiteratureExperimentSpec
from genevra.mechanisms.robustness import RobustnessAnalyzer, robustness_evolvability_association
from genevra.metrics.behavior import behavioral_signature
from genevra.metrics.diversity import EuclideanDistance
from genevra.metrics.evolvability import EvolvabilityAnalyzer
from genevra.organism.genome import ControllerArchitecture, Genome
from genevra.organism.learning import NoLearning
from genevra.organism.mutation import GaussianMutation
from genevra.organism.organism import OrganismConfig
from genevra.population_analysis.robustness_population import robustness_metric_association
from genevra.population_analysis.temporal_validation import leave_one_seed_out
from genevra.simulation.grid_world import GridWorldConfig
from genevra.simulation.types import Action

_GIT_COMMIT_UNAVAILABLE = "unavailable"

_VIEW_RADIUS = 1
_MEMORY_SIZE = 2
_INPUT_SIZE = (2 * _VIEW_RADIUS + 1) ** 2 * 2 + 2 + _MEMORY_SIZE


@dataclass(frozen=True)
class ScaleConfig:
    """The only thing that differs between `scale="quick"` and
    `scale="full"` — every analysis function downstream is identical."""

    case_a_seeds: tuple[int, ...]
    case_a_population: int
    case_a_generations: int
    boundary_seeds: tuple[int, ...]
    boundary_population: int
    boundary_generations: int
    boundary_periods: tuple[int, ...]
    robustness_n_genomes: int
    ecology_seeds: tuple[int, ...]


QUICK = ScaleConfig(
    case_a_seeds=(0, 1, 2, 3),
    case_a_population=8,
    case_a_generations=6,
    boundary_seeds=(0, 1, 2),
    boundary_population=6,
    boundary_generations=5,
    boundary_periods=(10, 30),
    robustness_n_genomes=4,
    ecology_seeds=(0, 1, 2),
)

FULL = ScaleConfig(
    case_a_seeds=tuple(range(8)),
    case_a_population=16,
    case_a_generations=15,
    boundary_seeds=(100, 101, 102, 103),
    boundary_population=12,
    boundary_generations=10,
    boundary_periods=(10, 20, 40),
    robustness_n_genomes=10,
    ecology_seeds=tuple(range(8)),
)


def _with_research_metrics(factory: Any) -> Any:
    """Wraps a condition factory so its `EvolutionConfig.metrics_level`
    is `RESEARCH` (needed for `learning_gene_stats`, used by RQ5/RQ8),
    without modifying `genevra.literature.cases` itself."""
    import dataclasses

    from genevra.metrics.trajectory import MetricsLevel

    def wrapped(seed: int) -> Any:
        config = factory(seed)
        evolution = dataclasses.replace(config.evolution, metrics_level=MetricsLevel.RESEARCH)
        return dataclasses.replace(config, evolution=evolution)

    return wrapped


def _git_commit() -> str:
    import subprocess

    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"], capture_output=True, text=True, timeout=5, check=False
        )
    except (OSError, subprocess.SubprocessError):  # pragma: no cover
        return _GIT_COMMIT_UNAVAILABLE
    return result.stdout.strip() if result.returncode == 0 else _GIT_COMMIT_UNAVAILABLE


def _config_hash(payload: dict[str, Any]) -> str:
    import hashlib

    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()[:16]


@dataclass
class EvidenceBuildResult:
    manifest: EvidenceManifest
    research_questions: list[ResearchQuestion]
    output_root: Path


def build_evidence_package(output_root: Path, scale: ScaleConfig = QUICK) -> EvidenceBuildResult:
    output_root.mkdir(parents=True, exist_ok=True)
    for sub in (
        "research_questions",
        "experiments",
        "data",
        "metrics",
        "statistics",
        "figures",
        "tables",
        "reports",
        "provenance",
        "configurations",
        "seeds",
        "supplementary",
        "checksums",
    ):
        (output_root / sub).mkdir(parents=True, exist_ok=True)

    manifest = EvidenceManifest()
    research_questions: list[ResearchQuestion] = []
    git_commit = _git_commit()

    # ---- RQ1 / RQ3 / RQ5 / RQ6 / RQ8: run CASE A once, reuse its raw
    # trajectories for four research questions rather than re-simulating. ----
    claim, spec, conditions = case_a_plasticity_evolvability_tradeoff(
        population_size=scale.case_a_population,
        generations=scale.case_a_generations,
        seeds=scale.case_a_seeds,
    )
    # RQ5/RQ8 need per-generation `learning_gene_stats`, which only the
    # RESEARCH metrics level records; wrap the case's condition factories
    # to request it without changing the case module itself.
    conditions = {
        condition_id: _with_research_metrics(factory)
        for condition_id, factory in conditions.items()
    }
    comparison = ComparisonRunner(conditions=conditions, seeds=spec.seeds).run()
    validation = validate_comparison(comparison)
    control_raw = comparison.conditions[spec.control_condition]
    treatment_raw = comparison.conditions[spec.treatment_condition]
    control_values = [
        v for v in (extract_metric(r, spec.primary_metric) for r in control_raw) if v is not None
    ]
    treatment_values = [
        v for v in (extract_metric(r, spec.primary_metric) for r in treatment_raw) if v is not None
    ]
    rng = np.random.default_rng(0)
    if validation.ok() and len(control_values) >= 2 and len(treatment_values) >= 2:
        label, perm, effect, observed_direction = classify_evidence(
            control_values, treatment_values, spec.expected_direction, spec.confidence_level, rng
        )
    else:
        label = ReproductionLabel.INVALID_EXPERIMENT
        perm = None
        effect = None
        observed_direction = None

    case_a_config_hash = _config_hash(spec.to_dict())
    (output_root / "configurations" / "case_a_spec.json").write_text(
        json.dumps(spec.to_dict(), indent=2)
    )
    (output_root / "seeds" / "case_a_seeds.json").write_text(json.dumps(list(spec.seeds), indent=2))

    # A compact, representative raw-data sample: the first two seeds of
    # each condition's trajectory, not every seed's full trajectory (size
    # discipline — the reproduction command regenerates the rest on demand).
    raw_sample = {
        spec.control_condition: control_raw[:2],
        spec.treatment_condition: treatment_raw[:2],
    }
    (output_root / "data" / "case_a_raw_sample.json").write_text(json.dumps(raw_sample, indent=2))
    manifest.add(
        EvidenceArtifact(
            artifact_id="case_a_raw_sample",
            artifact_type="data",
            research_question="RQ1",
            experiment_id=spec.spec_id,
            condition="both",
            seed_set=tuple(spec.seeds[:2]),
            source_data="genevra.analysis.comparison.ComparisonRunner",
            metric_ids=(spec.primary_metric,),
            analysis_version="genevra.literature.runner.v1",
            config_hash=case_a_config_hash,
            relative_path="data/case_a_raw_sample.json",
            limitations=(
                f"Only the first 2 of {len(spec.seeds)} seeds per condition are kept; the "
                "rest are reproducible via the exact command in README.md.",
            ),
            git_commit=git_commit,
        )
    )

    reproduction_result_dict = {
        "spec_id": spec.spec_id,
        "claim_id": spec.claim_id,
        "label": label.value,
        "n_control": len(control_values),
        "n_treatment": len(treatment_values),
        "observed_direction": observed_direction,
        "expected_direction": spec.expected_direction,
        "cohens_d": effect.cohens_d if effect is not None else None,
        "p_value": perm.p_value if perm is not None else None,
        "control_values": control_values,
        "treatment_values": treatment_values,
    }
    (output_root / "statistics" / "case_a_reproduction.json").write_text(
        json.dumps(reproduction_result_dict, indent=2)
    )
    manifest.add(
        EvidenceArtifact(
            artifact_id="case_a_reproduction_statistics",
            artifact_type="data",
            research_question="RQ1",
            experiment_id=spec.spec_id,
            condition="both",
            seed_set=tuple(spec.seeds),
            source_data="genevra.literature.runner.classify_evidence",
            metric_ids=(spec.primary_metric,),
            analysis_version="genevra.literature.runner.v1",
            config_hash=case_a_config_hash,
            relative_path="statistics/case_a_reproduction.json",
            git_commit=git_commit,
        )
    )

    # A real figure: fitness trajectory for one representative seed
    # (treatment condition, first completed seed).
    fig_dir = output_root / "figures"
    first_treatment = treatment_raw[0]
    fitness_meta = plot_fitness_trajectory(
        first_treatment["trajectory"], fig_dir, experiment_id="case_a_evolvable_learning_seed0"
    )
    diversity_meta = plot_diversity_trajectory(
        first_treatment["trajectory"], fig_dir, experiment_id="case_a_evolvable_learning_seed0"
    )
    novelty_meta = plot_novelty_trajectory(
        first_treatment["trajectory"], fig_dir, experiment_id="case_a_evolvable_learning_seed0"
    )
    for meta, metric_ids in (
        (fitness_meta, ("fitness_summary.mean",)),
        (diversity_meta, ("genotypic_diversity", "behavioral_diversity")),
        (novelty_meta, ("mean_novelty", "instantaneous_novelty")),
    ):
        for filename in meta.files:
            manifest.add(
                EvidenceArtifact(
                    artifact_id=meta.figure_id,
                    artifact_type="figure",
                    research_question="RQ1",
                    experiment_id="case_a_evolvable_learning_seed0",
                    condition=spec.treatment_condition,
                    seed_set=(spec.seeds[0],),
                    source_data=meta.data_source,
                    metric_ids=metric_ids,
                    analysis_version=meta.analysis_version,
                    config_hash=case_a_config_hash,
                    relative_path=f"figures/{filename}",
                    limitations=(meta.limitations,),
                    git_commit=git_commit,
                )
            )
        manifest.add(
            EvidenceArtifact(
                artifact_id=f"{meta.figure_id}_metadata",
                artifact_type="figure",
                research_question="RQ1",
                experiment_id="case_a_evolvable_learning_seed0",
                condition=spec.treatment_condition,
                seed_set=(spec.seeds[0],),
                source_data=meta.data_source,
                metric_ids=metric_ids,
                analysis_version=meta.analysis_version,
                config_hash=case_a_config_hash,
                relative_path=f"figures/{meta.figure_id}.json",
                git_commit=git_commit,
            )
        )

    rq1 = ResearchQuestion(
        question_id="RQ1",
        title="Environmental change, plasticity, and genetic-diversity retention",
        description="How does environmental change influence plasticity, learning, and "
        "evolvability (approximated here by standing genotypic diversity)?",
        hypothesis_ids=("case_a_plasticity_evolvability_tradeoff",),
        primary_outcome=spec.primary_metric,
        secondary_outcomes=(),
        experimental_conditions=(spec.control_condition, spec.treatment_condition),
        required_replication=spec.replication_required_seeds,
        statistical_plan=spec.statistical_test,
        evidence_status=_label_to_status(label),
        limitations=claim.known_limitations,
        experiment_ids=(spec.spec_id,),
    )
    research_questions.append(rq1)

    # ---- RQ3: does diversity at generation t predict novelty at t+k? ----
    lag = max(1, scale.case_a_generations // 3)
    x_by_seed: dict[int, list[float]] = {}
    y_by_seed: dict[int, list[float]] = {}
    for result, seed in zip(treatment_raw, spec.seeds, strict=False):
        trajectory = result.get("trajectory") or []
        if len(trajectory) <= lag:
            continue
        x_by_seed[seed] = [g["genotypic_diversity"] for g in trajectory[: len(trajectory) - lag]]
        y_by_seed[seed] = [g["instantaneous_novelty"] for g in trajectory[lag:]]
    lagged_result = leave_one_seed_out(x_by_seed, y_by_seed)
    (output_root / "statistics" / "rq3_lagged_prediction.json").write_text(
        json.dumps(
            {
                "predictor": "genotypic_diversity(t)",
                "target": f"instantaneous_novelty(t+{lag})",
                "lag": lag,
                **lagged_result.to_dict(),
            },
            indent=2,
        )
    )
    manifest.add(
        EvidenceArtifact(
            artifact_id="rq3_lagged_prediction",
            artifact_type="data",
            research_question="RQ3",
            experiment_id=spec.spec_id,
            condition=spec.treatment_condition,
            seed_set=tuple(sorted(x_by_seed)),
            source_data="genevra.population_analysis.temporal_validation.leave_one_seed_out",
            metric_ids=("genotypic_diversity", "instantaneous_novelty"),
            analysis_version="genevra.population_analysis.v1",
            config_hash=case_a_config_hash,
            relative_path="statistics/rq3_lagged_prediction.json",
            limitations=(
                "Held-out-seed sign agreement only; not a magnitude-calibrated forecast.",
            ),
            git_commit=git_commit,
        )
    )
    rq3_status = (
        EvidenceStatus.INSUFFICIENT_DATA
        if lagged_result.agreement_rate is None
        else (
            EvidenceStatus.SUPPORTED
            if lagged_result.agreement_rate >= 0.75
            else (
                EvidenceStatus.PARTIALLY_SUPPORTED
                if lagged_result.agreement_rate >= 0.5
                else EvidenceStatus.NOT_SUPPORTED
            )
        )
    )
    research_questions.append(
        ResearchQuestion(
            question_id="RQ3",
            title="Does current genetic diversity predict future novelty?",
            description="Leave-one-seed-out test of whether genotypic_diversity at "
            f"generation t predicts instantaneous_novelty at t+{lag}.",
            hypothesis_ids=("rq3_diversity_predicts_future_novelty",),
            primary_outcome="instantaneous_novelty",
            secondary_outcomes=(),
            experimental_conditions=(spec.treatment_condition,),
            required_replication=3,
            statistical_plan="leave_one_seed_out sign-agreement rate",
            evidence_status=rq3_status,
            limitations=(
                "Sign-agreement across seeds, not a magnitude/R^2 predictive benchmark.",
                f"n_seeds={lagged_result.n_seeds}; agreement_rate is None below 3 usable seeds.",
            ),
            experiment_ids=(spec.spec_id,),
        )
    )

    # ---- RQ5: cross-seed strategy convergence (final vs. initial spread). ----
    def _mean_strategy_vector(trajectory: list[dict[str, Any]], index: int) -> list[float] | None:
        stats = trajectory[index].get("learning_gene_stats")
        if not stats:
            return None
        return [s["mean"] for s in stats]

    initial_vectors = []
    final_vectors = []
    for result in treatment_raw:
        trajectory = result.get("trajectory") or []
        if not trajectory:
            continue
        initial = _mean_strategy_vector(trajectory, 0)
        final = _mean_strategy_vector(trajectory, -1)
        if initial is not None:
            initial_vectors.append(initial)
        if final is not None:
            final_vectors.append(final)

    def _mean_pairwise_distance(vectors: list[list[float]]) -> float | None:
        if len(vectors) < 2:
            return None
        arr = np.array(vectors)
        distances = [
            float(np.linalg.norm(arr[i] - arr[j]))
            for i in range(len(arr))
            for j in range(i + 1, len(arr))
        ]
        return float(np.mean(distances))

    initial_spread = _mean_pairwise_distance(initial_vectors)
    final_spread = _mean_pairwise_distance(final_vectors)
    # A degenerate initial_spread of exactly 0.0 (every seed starts from
    # the same deterministic initial gene value, before mutation has
    # acted) makes "converged relative to the initial spread" undefined
    # rather than a real negative finding — reported as such, not as a
    # false NOT_SUPPORTED.
    convergence_undefined = initial_spread is not None and initial_spread == 0.0
    convergence_payload = {
        "n_seeds_initial": len(initial_vectors),
        "n_seeds_final": len(final_vectors),
        "initial_mean_pairwise_strategy_distance": initial_spread,
        "final_mean_pairwise_strategy_distance": final_spread,
        "converged": (
            None
            if initial_spread is None or final_spread is None or convergence_undefined
            else bool(final_spread < initial_spread)
        ),
        "note": (
            "initial_mean_pairwise_strategy_distance is exactly 0.0 (deterministic gene "
            "initialization before mutation) — 'converged relative to initial spread' is "
            "undefined here, not a genuine negative finding."
            if convergence_undefined
            else ""
        ),
    }
    (output_root / "statistics" / "rq5_strategy_convergence.json").write_text(
        json.dumps(convergence_payload, indent=2)
    )
    manifest.add(
        EvidenceArtifact(
            artifact_id="rq5_strategy_convergence",
            artifact_type="data",
            research_question="RQ5",
            experiment_id=spec.spec_id,
            condition=spec.treatment_condition,
            seed_set=tuple(spec.seeds),
            source_data="case_a evolvable_learning trajectories, learning_gene_stats",
            metric_ids=("learning_gene_stats",),
            analysis_version="genevra.evidence.build.v1",
            config_hash=case_a_config_hash,
            relative_path="statistics/rq5_strategy_convergence.json",
            limitations=(
                "Cross-seed spread of the population MEAN strategy vector, not individual "
                "organisms; a small number of seeds limits how reliable 'converged' is.",
            ),
            git_commit=git_commit,
        )
    )
    rq5_status = (
        EvidenceStatus.INSUFFICIENT_DATA
        if convergence_payload["converged"] is None
        else (
            EvidenceStatus.SUPPORTED
            if convergence_payload["converged"]
            else EvidenceStatus.NOT_SUPPORTED
        )
    )
    research_questions.append(
        ResearchQuestion(
            question_id="RQ5",
            title="Do independent runs converge on similar learning strategies?",
            description="Compares the spread of independent seeds' mean learning-strategy "
            "vector at generation 0 vs. the final generation.",
            hypothesis_ids=("rq5_strategy_convergence",),
            primary_outcome="final_mean_pairwise_strategy_distance",
            secondary_outcomes=("initial_mean_pairwise_strategy_distance",),
            experimental_conditions=(spec.treatment_condition,),
            required_replication=3,
            statistical_plan="descriptive spread comparison (no significance test — 1 "
            "observation per seed, no repeated sampling to permute)",
            evidence_status=rq5_status,
            limitations=(
                "Descriptive only; a single spread comparison is not a hypothesis test.",
                "GENEVRA's mutation/selection noise is itself a 'shared environmental "
                "constraint' independent of learning — this does not distinguish "
                "convergence from that shared constraint (Phase 17.13's caveat).",
            ),
            experiment_ids=(spec.spec_id,),
        )
    )

    # ---- RQ6: literature comparison matrix (case A only, this round). ----
    comparison_rows = [
        ComparisonRow(
            claim=claim,
            result=_reproduction_result_obj(
                spec,
                label,
                control_values,
                treatment_values,
                perm,
                effect,
                observed_direction,
                validation,
            ),
        )
    ]
    matrix_csv = comparison_matrix_csv(comparison_rows)
    matrix_md = comparison_matrix_markdown(comparison_rows)
    (output_root / "tables" / "literature_comparison_matrix.csv").write_text(matrix_csv)
    (output_root / "tables" / "literature_comparison_matrix.md").write_text(matrix_md)
    for ext in ("csv", "md"):
        manifest.add(
            EvidenceArtifact(
                artifact_id="literature_comparison_matrix",
                artifact_type="table",
                research_question="RQ6",
                experiment_id=spec.spec_id,
                condition="both",
                seed_set=tuple(spec.seeds),
                source_data="genevra.literature.comparison_matrix",
                metric_ids=(spec.primary_metric,),
                analysis_version="genevra.literature.comparison_matrix.v1",
                config_hash=case_a_config_hash,
                relative_path=f"tables/literature_comparison_matrix.{ext}",
                limitations=(
                    "Only CASE A (Cuypers/Rutten/Hogeweg-inspired) is included this round; "
                    "CASE B/C/D were not re-run at evidence-package scale this session — "
                    "see docs/final_research_quality_gate.md.",
                ),
                git_commit=git_commit,
            )
        )
    research_questions.append(
        ResearchQuestion(
            question_id="RQ6",
            title="Which literature-inspired claims are supported in GENEVRA?",
            description="Structured comparison of GENEVRA's reproduction result against "
            "the literature-inspired claim(s) it was tested against.",
            hypothesis_ids=(claim.claim_id,),
            primary_outcome=spec.primary_metric,
            secondary_outcomes=(),
            experimental_conditions=(spec.control_condition, spec.treatment_condition),
            required_replication=spec.replication_required_seeds,
            statistical_plan=spec.statistical_test,
            evidence_status=_label_to_status(label),
            limitations=(
                "Only 1 of GENEVRA's 4 literature cases (A/B/C/D) is represented in this "
                "evidence package; B/C/D remain NOT_TESTED here (machinery exists, not run "
                "at this scale this session).",
            ),
            experiment_ids=(spec.spec_id,),
        )
    )

    # ---- RQ8: discovery engine integration (phenomenon -> hypothesis -> follow-up). ----
    detector = PhenomenonDetector()
    observations = []
    for result, seed in zip(treatment_raw, spec.seeds, strict=False):
        trajectory = result.get("trajectory") or []
        if trajectory:
            observations.extend(
                detector.detect(trajectory, experiment="case_a_evolvable", seed=seed)
            )
    discovery_hypotheses = hypotheses_from_recurring_phenomena(observations, min_seed_count=2)
    followups = [generate_followup_experiment(h) for h in discovery_hypotheses[:1]]
    discovery_payload = {
        "n_phenomena_observed": len(observations),
        "observations": [
            {
                "name": o.name,
                "experiment": o.experiment,
                "seed": o.seed,
                "description": o.description,
            }
            for o in observations
        ],
        "n_recurring_hypotheses": len(discovery_hypotheses),
        "hypotheses": [
            {"hypothesis_id": h.hypothesis_id, "statement": h.statement}
            for h in discovery_hypotheses
        ],
        "followup_proposals": [
            {
                "hypothesis_id": f.hypothesis_id,
                "independent_variable": f.independent_variable,
                "conditions": list(f.conditions),
                "sample_size": f.sample_size,
                "validation_errors": f.validate(),
                "status": "DISCOVERY-GENERATED, not executed — a proposal only",
            }
            for f in followups
        ],
    }
    (output_root / "statistics" / "rq8_discovery.json").write_text(
        json.dumps(discovery_payload, indent=2)
    )
    manifest.add(
        EvidenceArtifact(
            artifact_id="rq8_discovery",
            artifact_type="data",
            research_question="RQ8",
            experiment_id=spec.spec_id,
            condition=spec.treatment_condition,
            seed_set=tuple(spec.seeds),
            source_data="genevra.discovery.phenomena/hypothesis/followup",
            metric_ids=(),
            analysis_version="genevra.discovery.v1",
            config_hash=case_a_config_hash,
            relative_path="statistics/rq8_discovery.json",
            limitations=(
                "Proposed follow-up experiments were generated but NOT executed this "
                "session — they remain proposals, not confirmatory results.",
            ),
            git_commit=git_commit,
        )
    )
    rq8_status = (
        EvidenceStatus.INSUFFICIENT_DATA if not discovery_hypotheses else EvidenceStatus.NOT_TESTED
    )
    research_questions.append(
        ResearchQuestion(
            question_id="RQ8",
            title="Can the discovery engine generate testable follow-up hypotheses?",
            description="Runs PhenomenonDetector across CASE A's seeds, groups recurring "
            "phenomena into hypotheses, and generates (but does not execute) a follow-up "
            "experiment proposal.",
            hypothesis_ids=tuple(h.hypothesis_id for h in discovery_hypotheses),
            primary_outcome="n_recurring_hypotheses",
            secondary_outcomes=(),
            experimental_conditions=(spec.treatment_condition,),
            required_replication=2,
            statistical_plan="recurrence across >= 2 independent seeds (no significance test)",
            evidence_status=rq8_status,
            limitations=(
                "'NOT_TESTED' here means hypotheses were generated but the generated "
                "follow-up experiment itself was not executed — the pipeline runs "
                "end-to-end, but the loop was not closed with a real follow-up run.",
            ),
            experiment_ids=(spec.spec_id,),
        )
    )

    # ---- RQ7: boundary-condition sweep over CASE A's environmental period. ----
    def _build_case(period: float) -> Any:
        return case_a_plasticity_evolvability_tradeoff(
            population_size=scale.boundary_population,
            generations=scale.boundary_generations,
            seeds=scale.boundary_seeds,
            period=int(period),
        )

    boundary_result = run_boundary_sweep(
        "environmental_change_period",
        _build_case,
        [float(p) for p in scale.boundary_periods],
        np.random.default_rng(1),
    )
    (output_root / "statistics" / "rq7_boundary_sweep.json").write_text(
        json.dumps(boundary_result.to_dict(), indent=2)
    )
    manifest.add(
        EvidenceArtifact(
            artifact_id="rq7_boundary_sweep",
            artifact_type="data",
            research_question="RQ7",
            experiment_id="case_a_boundary_sweep",
            condition="swept:environmental_change_period",
            seed_set=tuple(scale.boundary_seeds),
            source_data="genevra.literature.boundary_search.run_boundary_sweep",
            metric_ids=(spec.primary_metric,),
            analysis_version="genevra.literature.boundary_search.v1",
            config_hash=_config_hash({"periods": scale.boundary_periods}),
            relative_path="statistics/rq7_boundary_sweep.json",
            limitations=(
                f"Only {len(scale.boundary_periods)} period values tested with "
                f"{len(scale.boundary_seeds)} seeds each — a coarse sweep, not a "
                "continuous response surface.",
            ),
            git_commit=git_commit,
        )
    )
    transitions = boundary_result.transitions()
    research_questions.append(
        ResearchQuestion(
            question_id="RQ7",
            title="Under what environmental-change rates does the CASE A pattern change?",
            description="Sweeps the environmental-change period parameter and records the "
            "reproduction label found at each value.",
            hypothesis_ids=("rq7_boundary_condition",),
            primary_outcome=spec.primary_metric,
            secondary_outcomes=(),
            experimental_conditions=tuple(f"period={p}" for p in scale.boundary_periods),
            required_replication=len(scale.boundary_seeds),
            statistical_plan="per-value classify_evidence label; transitions = consecutive "
            "differing labels",
            evidence_status=(
                EvidenceStatus.PARTIALLY_SUPPORTED if transitions else EvidenceStatus.INCONCLUSIVE
            ),
            limitations=(
                "A coarse, discrete sweep over one GENEVRA-exposed parameter approximating "
                "the source paper's continuous environmental-change-rate axis.",
            ),
            experiment_ids=("case_a_boundary_sweep",),
        )
    )

    # ---- RQ2: robustness vs. evolvability, seed-as-unit. ----
    robustness_by_seed: dict[int, float] = {}
    evolvability_by_seed: dict[int, float] = {}
    per_genome_robustness: list[float] = []
    per_genome_evolvability: list[float] = []
    env_config = GridWorldConfig(width=8, height=8, view_radius=_VIEW_RADIUS, max_steps=30)
    organism_config = OrganismConfig(
        view_radius=_VIEW_RADIUS, memory_size=_MEMORY_SIZE, initial_energy=15.0
    )
    architecture = ControllerArchitecture(
        input_size=_INPUT_SIZE, hidden_size=6, output_size=len(Action)
    )
    mutation_operator = GaussianMutation()
    for seed in range(scale.robustness_n_genomes):
        genome_rng = np.random.default_rng(seed)
        genome = Genome.random(architecture, genome_rng)
        genome.mutation_genes[:] = [0.5, 0.3]

        robustness_analyzer = RobustnessAnalyzer(
            environment_config=env_config,
            organism_config=organism_config,
            learning_rule=NoLearning(),
            mutation_operator=mutation_operator,
            distance=EuclideanDistance(),
            num_samples=5,
            max_steps=30,
        )
        profile = robustness_analyzer.analyze(genome, np.random.default_rng(seed + 1000))

        def _behavioral_evaluator(g: Genome, seed: int = seed) -> Any:
            observations = run_single_lifetime(
                g, env_config, organism_config, NoLearning(), seed + 2000, seed + 3000, 30
            )
            return behavioral_signature(observations)

        evolvability_analyzer = EvolvabilityAnalyzer(
            mutation_operator=mutation_operator,
            behavioral_evaluator=_behavioral_evaluator,
            distance=EuclideanDistance(),
            num_samples=8,
        )
        evolvability_report = evolvability_analyzer.analyze(
            genome, np.random.default_rng(seed + 4000)
        )

        robustness_by_seed[seed] = profile.genetic.mean
        evolvability_by_seed[seed] = evolvability_report.mean_behavioral_distance
        per_genome_robustness.append(profile.genetic.mean)
        per_genome_evolvability.append(evolvability_report.mean_behavioral_distance)

    per_genome_association = robustness_evolvability_association(
        per_genome_robustness, per_genome_evolvability
    )
    seed_level_association = robustness_metric_association(robustness_by_seed, evolvability_by_seed)
    rq2_payload = {
        "n_genomes": scale.robustness_n_genomes,
        "robustness_by_seed": robustness_by_seed,
        "evolvability_by_seed": evolvability_by_seed,
        "per_genome_pearson_r": per_genome_association,
        "seed_level_pearson_r": seed_level_association,
    }
    (output_root / "statistics" / "rq2_robustness_evolvability.json").write_text(
        json.dumps(rq2_payload, indent=2)
    )
    manifest.add(
        EvidenceArtifact(
            artifact_id="rq2_robustness_evolvability",
            artifact_type="data",
            research_question="RQ2",
            experiment_id="rq2_robustness_evolvability",
            condition="n/a (per-genome sampling)",
            seed_set=tuple(range(scale.robustness_n_genomes)),
            source_data="genevra.mechanisms.robustness / genevra.metrics.evolvability",
            metric_ids=("robustness", "evolvability_mean_behavioral_distance"),
            analysis_version="genevra.mechanisms.v1",
            config_hash=_config_hash({"n_genomes": scale.robustness_n_genomes}),
            relative_path="statistics/rq2_robustness_evolvability.json",
            limitations=(
                "One representative sampled genotype per seed, not a full evolved "
                "population per seed; a small n_genomes limits statistical power.",
            ),
            git_commit=git_commit,
        )
    )
    rq2_fig_meta = plot_robustness_vs_evolvability(
        per_genome_robustness,
        per_genome_evolvability,
        fig_dir,
        experiment_id="rq2_robustness_evolvability",
    )
    for filename in rq2_fig_meta.files:
        manifest.add(
            EvidenceArtifact(
                artifact_id=rq2_fig_meta.figure_id,
                artifact_type="figure",
                research_question="RQ2",
                experiment_id="rq2_robustness_evolvability",
                condition="n/a",
                seed_set=tuple(range(scale.robustness_n_genomes)),
                source_data=rq2_fig_meta.data_source,
                metric_ids=("robustness", "evolvability_mean_behavioral_distance"),
                analysis_version=rq2_fig_meta.analysis_version,
                config_hash=_config_hash({"n_genomes": scale.robustness_n_genomes}),
                relative_path=f"figures/{filename}",
                git_commit=git_commit,
            )
        )
    manifest.add(
        EvidenceArtifact(
            artifact_id=f"{rq2_fig_meta.figure_id}_metadata",
            artifact_type="figure",
            research_question="RQ2",
            experiment_id="rq2_robustness_evolvability",
            condition="n/a",
            seed_set=tuple(range(scale.robustness_n_genomes)),
            source_data=rq2_fig_meta.data_source,
            metric_ids=("robustness", "evolvability_mean_behavioral_distance"),
            analysis_version=rq2_fig_meta.analysis_version,
            config_hash=_config_hash({"n_genomes": scale.robustness_n_genomes}),
            relative_path=f"figures/{rq2_fig_meta.figure_id}.json",
            git_commit=git_commit,
        )
    )
    rq2_status = (
        EvidenceStatus.INSUFFICIENT_DATA
        if seed_level_association is None
        else (
            EvidenceStatus.PARTIALLY_SUPPORTED
            if abs(seed_level_association) >= 0.3
            else EvidenceStatus.INCONCLUSIVE
        )
    )
    research_questions.append(
        ResearchQuestion(
            question_id="RQ2",
            title="How does robustness relate to evolvability?",
            description="Correlates genetic robustness with mutational-neighborhood "
            "evolvability across independently sampled genotypes (seed = replication unit).",
            hypothesis_ids=("rq2_robustness_evolvability_association",),
            primary_outcome="evolvability_mean_behavioral_distance",
            secondary_outcomes=(),
            experimental_conditions=("n/a: correlational design, not conditions",),
            required_replication=3,
            statistical_plan="Pearson correlation at the seed level (>=3 seeds required)",
            evidence_status=rq2_status,
            limitations=(
                "Association only; direction of causality (if any) is not established.",
                "This measures 'current evolvability' (mutational neighborhood), not "
                "'future evolvability realized over generations' — a genuinely stronger "
                "claim this evidence package does not attempt.",
            ),
            experiment_ids=("rq2_robustness_evolvability",),
        )
    )

    # ---- RQ4: ecology (isolated vs. shared), reusing experiments/exp1. ----
    import importlib.util

    exp1_path = Path(__file__).resolve().parents[3] / "experiments" / "exp1_isolated_vs_shared.py"
    spec_mod = importlib.util.spec_from_file_location("exp1_isolated_vs_shared", exp1_path)
    assert spec_mod is not None and spec_mod.loader is not None
    exp1 = importlib.util.module_from_spec(spec_mod)
    spec_mod.loader.exec_module(exp1)

    isolated_values = [exp1.isolated_final_diversity(s) for s in scale.ecology_seeds]
    shared_values = [exp1.shared_final_diversity(s) for s in scale.ecology_seeds]
    isolated_values = [v for v in isolated_values if v == v]  # drop NaN
    shared_values = [v for v in shared_values if v == v]
    ecology_perm = (
        permutation_test(shared_values, isolated_values, np.random.default_rng(2))
        if len(isolated_values) >= 2 and len(shared_values) >= 2
        else None
    )
    ecology_effect = (
        cohens_d(shared_values, isolated_values)
        if len(isolated_values) >= 2 and len(shared_values) >= 2
        else None
    )
    ecology_payload = {
        "seeds": list(scale.ecology_seeds),
        "isolated_final_genotypic_diversity": isolated_values,
        "shared_final_genotypic_diversity": shared_values,
        "observed_difference": ecology_perm.observed_difference if ecology_perm else None,
        "p_value": ecology_perm.p_value if ecology_perm else None,
        "cohens_d": ecology_effect.cohens_d if ecology_effect else None,
    }
    (output_root / "statistics" / "rq4_ecology.json").write_text(
        json.dumps(ecology_payload, indent=2)
    )
    manifest.add(
        EvidenceArtifact(
            artifact_id="rq4_ecology",
            artifact_type="data",
            research_question="RQ4",
            experiment_id="exp1_isolated_vs_shared",
            condition="isolated_vs_shared",
            seed_set=tuple(scale.ecology_seeds),
            source_data="experiments/exp1_isolated_vs_shared.py",
            metric_ids=("genotypic_diversity",),
            analysis_version="genevra.analysis.aggregation.v1",
            config_hash=_config_hash({"seeds": scale.ecology_seeds}),
            relative_path="statistics/rq4_ecology.json",
            limitations=(
                "Isolated (discrete-generation, one-organism-per-episode) and shared "
                "(continuous, multi-agent) conditions use different simulation engines; "
                "final genotypic_diversity is the one metric directly comparable across "
                "both, per experiments/exp1_isolated_vs_shared.py's own docstring.",
            ),
            git_commit=git_commit,
        )
    )
    # Mirrors genevra.literature.runner.classify_evidence's significance/
    # effect-size thresholds (alpha=0.1, |d|<0.2 negligible, <0.5 small-
    # to-medium, >=0.5 medium-or-larger) rather than significance alone —
    # a large p-value-only threshold would understate a large real effect.
    if ecology_perm is None or ecology_effect is None:
        rq4_status = EvidenceStatus.INSUFFICIENT_DATA
    elif ecology_perm.p_value >= 0.1:
        rq4_status = EvidenceStatus.INCONCLUSIVE
    elif abs(ecology_effect.cohens_d) < 0.2:
        rq4_status = EvidenceStatus.NOT_SUPPORTED
    elif abs(ecology_effect.cohens_d) < 0.5:
        rq4_status = EvidenceStatus.PARTIALLY_SUPPORTED
    else:
        rq4_status = EvidenceStatus.SUPPORTED
    research_questions.append(
        ResearchQuestion(
            question_id="RQ4",
            title="Does ecological interaction structure affect evolutionary dynamics?",
            description="Compares final genotypic diversity between isolated "
            "(single-organism-per-episode) and shared (multi-agent, resource-competing) "
            "conditions.",
            hypothesis_ids=("rq4_isolated_vs_shared_diversity",),
            primary_outcome="genotypic_diversity",
            secondary_outcomes=(),
            experimental_conditions=("isolated", "shared"),
            required_replication=len(scale.ecology_seeds),
            statistical_plan="permutation_test + cohens_d, seed as replication unit",
            evidence_status=rq4_status,
            limitations=(
                "An infrastructure-comparable proxy metric across two different engines, "
                "not a within-one-engine controlled ecology manipulation.",
            ),
            experiment_ids=("exp1_isolated_vs_shared",),
        )
    )

    # ---- Development/validation seed split (Phase 19.4). ----
    # A real, non-overlapping partition of the seeds this build actually
    # executed (case_a ∪ ecology) — not a separate held-out run. See
    # docs/final_research_quality_gate.md: the analysis choices above
    # (lag k, status thresholds) were fixed in code, not tuned against
    # this specific seed pool, but were not designed on a formally
    # separate "development" seed set before this split existed either;
    # this is a partition for future validation-style reruns, not
    # evidence that today's numbers already followed a dev/val protocol.
    all_seeds = sorted(set(scale.case_a_seeds) | set(scale.ecology_seeds))
    n_validation = max(1, len(all_seeds) // 4)
    seed_split = split_seeds(list(all_seeds), n_validation)
    (output_root / "seeds" / "development_validation_split.json").write_text(
        json.dumps(seed_split.to_dict(), indent=2)
    )

    # ---- Metric registry + robustness classification. ----
    (output_root / "metrics" / "metric_registry.json").write_text(
        json.dumps({k: v.to_dict() for k, v in REGISTRY.items()}, indent=2)
    )
    rq2_robustness_report = classify_robustness(
        "rq2_robustness_evolvability_association",
        {f"genome_{i}": v for i, v in enumerate(per_genome_robustness)},
    )
    (output_root / "statistics" / "rq2_sensitivity.json").write_text(
        json.dumps(rq2_robustness_report.to_dict(), indent=2)
    )

    # ---- negative/inconclusive results, master matrix, reports. ----
    _write_master_matrix(output_root, research_questions)
    _write_negative_results_report(output_root, research_questions)
    _write_rq_reports(output_root, research_questions)
    for rq in research_questions:
        (output_root / "research_questions" / f"{rq.question_id}.json").write_text(
            json.dumps(rq.to_dict(), indent=2)
        )

    all_rq_ids = tuple(rq.question_id for rq in research_questions)
    all_seeds_used = tuple(
        sorted(set(scale.case_a_seeds) | set(scale.ecology_seeds) | set(scale.boundary_seeds))
    )
    for ext in ("csv", "md"):
        manifest.add(
            EvidenceArtifact(
                artifact_id="research_question_matrix",
                artifact_type="table",
                research_question="ALL",
                experiment_id="research_question_matrix",
                condition="all",
                seed_set=all_seeds_used,
                source_data="genevra.evidence.research_question (aggregated across all RQs)",
                metric_ids=(),
                analysis_version="genevra.evidence.build.v1",
                config_hash=_config_hash({"rq_ids": all_rq_ids}),
                relative_path=f"tables/research_question_matrix.{ext}",
                git_commit=git_commit,
            )
        )
    manifest.add(
        EvidenceArtifact(
            artifact_id="negative_and_inconclusive_results",
            artifact_type="report",
            research_question="ALL",
            experiment_id="negative_and_inconclusive_results",
            condition="all",
            seed_set=all_seeds_used,
            source_data="genevra.evidence.research_question (aggregated across all RQs)",
            metric_ids=(),
            analysis_version="genevra.evidence.build.v1",
            config_hash=_config_hash({"rq_ids": all_rq_ids}),
            relative_path="reports/negative_and_inconclusive_results.md",
            git_commit=git_commit,
        )
    )
    for rq in research_questions:
        manifest.add(
            EvidenceArtifact(
                artifact_id=f"{rq.question_id}_report",
                artifact_type="report",
                research_question=rq.question_id,
                experiment_id=rq.experiment_ids[0] if rq.experiment_ids else "n/a",
                condition="; ".join(rq.experimental_conditions),
                seed_set=all_seeds_used,
                source_data="genevra.evidence.research_question",
                metric_ids=(rq.primary_outcome,),
                analysis_version="genevra.evidence.build.v1",
                config_hash=_config_hash({"question_id": rq.question_id}),
                relative_path=f"reports/{rq.question_id}.md",
                git_commit=git_commit,
            )
        )

    # ---- checksums (over everything just written, excluding the manifest itself). ----
    manifest.save(output_root / "manifest.json")
    all_files = [p for p in output_root.rglob("*") if p.is_file() and p.name != "manifest.sha256"]
    write_checksum_manifest(output_root, all_files, output_root / "checksums" / "manifest.sha256")

    return EvidenceBuildResult(
        manifest=manifest, research_questions=research_questions, output_root=output_root
    )


def _label_to_status(label: ReproductionLabel) -> EvidenceStatus:
    return {
        ReproductionLabel.SUPPORTED: EvidenceStatus.SUPPORTED,
        ReproductionLabel.PARTIALLY_SUPPORTED: EvidenceStatus.PARTIALLY_SUPPORTED,
        ReproductionLabel.NOT_SUPPORTED: EvidenceStatus.NOT_SUPPORTED,
        ReproductionLabel.CONTRADICTED: EvidenceStatus.CONTRADICTED,
        ReproductionLabel.INCONCLUSIVE: EvidenceStatus.INCONCLUSIVE,
        ReproductionLabel.INVALID_EXPERIMENT: EvidenceStatus.INSUFFICIENT_DATA,
    }[label]


def _reproduction_result_obj(
    spec: LiteratureExperimentSpec,
    label: ReproductionLabel,
    control_values: list[float],
    treatment_values: list[float],
    perm: PermutationTestResult | None,
    effect: EffectSizeResult | None,
    observed_direction: str | None,
    validation: ComparisonValidation,
) -> ReproductionResult:
    return ReproductionResult(
        spec_id=spec.spec_id,
        claim_id=spec.claim_id,
        label=label,
        control_values=tuple(control_values),
        treatment_values=tuple(treatment_values),
        permutation=perm,
        effect_size=effect,
        observed_direction=observed_direction,
        expected_direction=spec.expected_direction,
        validation=validation,
        n_control=len(control_values),
        n_treatment=len(treatment_values),
    )


def _write_master_matrix(output_root: Path, research_questions: list[ResearchQuestion]) -> None:
    columns = (
        "question_id",
        "title",
        "hypothesis_ids",
        "experiment_ids",
        "required_replication",
        "primary_outcome",
        "statistical_plan",
        "evidence_status",
    )
    rows = [
        {
            "question_id": rq.question_id,
            "title": rq.title,
            "hypothesis_ids": "; ".join(rq.hypothesis_ids),
            "experiment_ids": "; ".join(rq.experiment_ids),
            "required_replication": rq.required_replication,
            "primary_outcome": rq.primary_outcome,
            "statistical_plan": rq.statistical_plan,
            "evidence_status": rq.evidence_status.value,
        }
        for rq in research_questions
    ]
    (output_root / "tables" / "research_question_matrix.csv").write_text(to_csv(rows, columns))
    (output_root / "tables" / "research_question_matrix.md").write_text(to_markdown(rows, columns))


def _write_negative_results_report(
    output_root: Path, research_questions: list[ResearchQuestion]
) -> None:
    negative = [
        rq
        for rq in research_questions
        if rq.evidence_status
        in (
            EvidenceStatus.NOT_SUPPORTED,
            EvidenceStatus.CONTRADICTED,
            EvidenceStatus.INCONCLUSIVE,
            EvidenceStatus.INSUFFICIENT_DATA,
        )
    ]
    lines = [
        "# Negative and Inconclusive Results",
        "",
        "GENEVRA's evidence package preserves every research question's actual "
        "outcome, including negative and inconclusive ones, rather than reporting "
        "only questions that produced a clean supporting result.",
        "",
    ]
    if not negative:
        lines.append(
            "No research question in this evidence package resolved to "
            "NOT_SUPPORTED / CONTRADICTED / INCONCLUSIVE / INSUFFICIENT_DATA."
        )
    for rq in negative:
        lines.append(f"## {rq.question_id}: {rq.title}")
        lines.append(f"Status: **{rq.evidence_status.value}**")
        lines.append(rq.description)
        for limitation in rq.limitations:
            lines.append(f"- {limitation}")
        lines.append("")
    (output_root / "reports" / "negative_and_inconclusive_results.md").write_text("\n".join(lines))


def _write_rq_reports(output_root: Path, research_questions: list[ResearchQuestion]) -> None:
    for rq in research_questions:
        lines = [
            f"# {rq.question_id}: {rq.title}",
            "",
            "## Research Question",
            rq.description,
            "",
            "## Hypotheses",
            ", ".join(rq.hypothesis_ids) or "(none named)",
            "",
            "## Experimental Design",
            f"Conditions: {', '.join(rq.experimental_conditions)}",
            f"Required replication: {rq.required_replication} independent seeds",
            "",
            "## Statistical Analysis",
            rq.statistical_plan,
            "",
            f"## Status: {rq.evidence_status.value}",
            "",
            "## Limitations",
        ]
        lines.extend(f"- {limitation}" for limitation in rq.limitations)
        lines.append("")
        lines.append("## Reproduction")
        lines.append(f"Experiment ID(s): {', '.join(rq.experiment_ids) or 'n/a'}")
        (output_root / "reports" / f"{rq.question_id}.md").write_text("\n".join(lines))


__all__ = ["ScaleConfig", "QUICK", "FULL", "EvidenceBuildResult", "build_evidence_package"]
