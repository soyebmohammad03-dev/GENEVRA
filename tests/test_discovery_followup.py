from genevra.discovery.followup import generate_followup_experiment
from genevra.discovery.hypothesis import Hypothesis


def _hypothesis() -> Hypothesis:
    return Hypothesis(
        hypothesis_id="h1",
        statement="stmt",
        independent_variable="mutation_sigma",
        dependent_variable="novelty_auc",
        predicted_direction="positive",
        supporting_observations=(),
        conflicting_observations=(),
        source_experiment_ids=(),
        evidence_score=0.5,
    )


def test_followup_proposal_is_well_formed() -> None:
    proposal = generate_followup_experiment(_hypothesis())
    assert proposal.hypothesis_id == "h1"
    assert proposal.independent_variable == "mutation_sigma"
    assert "novelty_auc" in proposal.dependent_variables
    assert proposal.validate() == []


def test_followup_seed_start_avoids_overlap_with_discovery_seeds() -> None:
    proposal = generate_followup_experiment(_hypothesis(), seed_start=10_000)
    assert "10000" in proposal.seed_policy


def test_validate_flags_too_few_seeds() -> None:
    proposal = generate_followup_experiment(_hypothesis(), sample_size=1)
    problems = proposal.validate()
    assert any("sample_size" in p for p in problems)


def test_validate_flags_zero_generation_budget() -> None:
    proposal = generate_followup_experiment(_hypothesis(), generation_budget=0)
    problems = proposal.validate()
    assert any("generation_budget" in p for p in problems)
