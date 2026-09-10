from genevra.discovery.followup import generate_followup_experiment
from genevra.discovery.hypothesis import Hypothesis
from genevra.discovery.loop import HypothesisEvaluation
from genevra.discovery.phenomena import PhenomenonObservation
from genevra.discovery.report import build_discovery_report


def _hypothesis() -> Hypothesis:
    return Hypothesis(
        hypothesis_id="h1",
        statement="mutation_sigma may predict novelty_auc",
        independent_variable="mutation_sigma",
        dependent_variable="novelty_auc",
        predicted_direction="positive",
        supporting_observations=("rho=0.6",),
        conflicting_observations=(),
        source_experiment_ids=("exp1",),
        evidence_score=0.7,
    )


def test_report_to_dict_has_all_sections() -> None:
    hypothesis = _hypothesis()
    report = build_discovery_report(
        observed_phenomena=[
            PhenomenonObservation(name="n", description="d", experiment="exp1", seed=0, evidence={})
        ],
        candidate_hypotheses=[hypothesis],
        contradicting_evidence=[],
        follow_up_experiments=[generate_followup_experiment(hypothesis)],
        hypothesis_evaluations=[
            HypothesisEvaluation(hypothesis_id="h1", label="inconclusive", reason="r")
        ],
    )
    data = report.to_dict()
    assert set(data.keys()) == {
        "observed_phenomena",
        "candidate_hypotheses",
        "contradicting_evidence",
        "follow_up_experiments",
        "hypothesis_evaluations",
        "limitations",
    }
    assert data["limitations"]


def test_report_to_text_never_claims_discovery() -> None:
    report = build_discovery_report([], [_hypothesis()], [], [], [])
    text = report.to_text()
    assert "discovered a" not in text.lower()
    assert "Limitations" in text
