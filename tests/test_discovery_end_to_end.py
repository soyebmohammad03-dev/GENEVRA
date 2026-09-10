"""End-to-end: EXPERIMENT -> ANALYSIS -> PHENOMENON -> HYPOTHESIS ->
FOLLOW-UP CONFIGURATION, over deterministic fixture trajectories (not a
noisy stochastic simulation run — Phase 9/10 testing guidance)."""

from __future__ import annotations

import numpy as np

from genevra.discovery.correlation import RunSummary, correlation_discovery
from genevra.discovery.followup import generate_followup_experiment
from genevra.discovery.hypothesis import (
    hypotheses_from_correlations,
    hypotheses_from_recurring_phenomena,
    rank_hypotheses,
)
from genevra.discovery.multiple_testing import benjamini_hochberg
from genevra.discovery.phenomena import PhenomenonDetector


def _fixture_trajectory(seed: int, mutation_sigma: float) -> list[dict]:
    """A deterministic fixture: novelty rises proportionally to
    `mutation_sigma` while fitness stays flat — engineered so
    `NoveltyWithoutFitnessGainRule` and the mutation_sigma/novelty
    correlation are both, by construction, real in this fixture."""
    return [
        {
            "generation": g,
            "fitness_summary": {"mean": 1.0 + 0.001 * seed},
            "instantaneous_novelty": 0.1 + g * 0.02 * mutation_sigma,
            "genotypic_diversity": 0.5,
        }
        for g in range(10)
    ]


def test_experiment_to_followup_pipeline() -> None:
    # EXPERIMENT: five fixture runs with increasing mutation_sigma.
    seeds = list(range(5))
    trajectories = {
        seed: _fixture_trajectory(seed, mutation_sigma=0.2 * (seed + 1)) for seed in seeds
    }

    # ANALYSIS + PHENOMENON: detect phenomena in each run.
    detector = PhenomenonDetector()
    all_observations = [
        observation
        for seed in seeds
        for observation in detector.detect(trajectories[seed], "exp1", seed)
    ]
    assert any(o.name == "novelty_without_fitness_gain" for o in all_observations)

    # ANALYSIS: build one row per (experiment, seed) run for correlation
    # discovery, respecting the "one row per run" unit of analysis.
    runs = [
        RunSummary(
            experiment="exp1",
            seed=seed,
            variables={
                "mutation_sigma": 0.2 * (seed + 1),
                "final_novelty": trajectories[seed][-1]["instantaneous_novelty"],
            },
        )
        for seed in seeds
    ]
    rng = np.random.default_rng(0)
    correlations = correlation_discovery(runs, [("mutation_sigma", "final_novelty")], rng)
    fdr = benjamini_hochberg([c.p_value for c in correlations])

    # HYPOTHESIS: generate from both the correlation and the recurring
    # phenomenon.
    from_correlations = hypotheses_from_correlations(correlations, fdr, effect_size_threshold=0.3)
    from_phenomena = hypotheses_from_recurring_phenomena(all_observations, min_seed_count=2)
    hypotheses = rank_hypotheses(from_correlations + from_phenomena)
    assert hypotheses, "the engineered fixture must produce at least one hypothesis"

    # FOLLOW-UP CONFIGURATION: every hypothesis proposes a validated,
    # non-executed follow-up experiment.
    proposals = [generate_followup_experiment(h) for h in hypotheses]
    for proposal in proposals:
        assert proposal.validate() == []
        assert proposal.hypothesis_id in {h.hypothesis_id for h in hypotheses}
