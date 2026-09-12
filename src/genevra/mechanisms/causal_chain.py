"""Phase 13.11: a named causal-chain scaffold whose links are tested
independently, never inferred as a whole from one correlation.

`CAUSAL_CHAIN` documents the chain from the spec (environmental
volatility -> learning strategy -> lifetime adaptation -> selection ->
genetic composition -> mutational landscape -> future evolvability ->
innovation) as a sequence of named links, each pointing at the existing
or new analysis capable of testing *that one arrow* — e.g. the
env-volatility -> learning-strategy link is tested by comparing evolved
`LearningStrategy` distributions across conditions with different
environmental dynamics
(`genevra.mechanisms.learning_strategy_evolution.strategy_environment_dependence`),
not by looking at the whole chain's endpoints and asserting the arrows
in between. `test_link` dispatches to whichever tester a link names and
always returns evidence + a status, never a chain-wide verdict.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class CausalLink:
    link_id: str
    from_node: str
    to_node: str
    description: str
    testable_via: str
    """Name of the existing/new analysis capable of testing this one
    link (a module.function reference, e.g.
    'genevra.mechanisms.learning_strategy_evolution.strategy_environment_dependence')."""


CAUSAL_CHAIN: tuple[CausalLink, ...] = (
    CausalLink(
        link_id="volatility_to_strategy",
        from_node="environmental_volatility",
        to_node="learning_strategy",
        description=(
            "Does environmental volatility select for a different evolved LearningStrategy?"
        ),
        testable_via=(
            "genevra.mechanisms.learning_strategy_evolution.strategy_environment_dependence"
        ),
    ),
    CausalLink(
        link_id="strategy_to_adaptation",
        from_node="learning_strategy",
        to_node="lifetime_adaptation",
        description="Does the evolved learning strategy affect the lifetime AdaptationCurve?",
        testable_via="genevra.metrics.adaptation.compute_adaptation_curve",
    ),
    CausalLink(
        link_id="adaptation_to_selection",
        from_node="lifetime_adaptation",
        to_node="selection",
        description="Does higher lifetime adaptation (learning_gain) predict selection/survival?",
        testable_via="genevra.analysis.tradeoff.summarize_tradeoff",
    ),
    CausalLink(
        link_id="selection_to_genetic_composition",
        from_node="selection",
        to_node="genetic_composition",
        description=(
            "Does selection shift the population's genotype/strategy distribution over generations?"
        ),
        testable_via="genevra.analysis.strategy_clustering.strategy_turnover",
    ),
    CausalLink(
        link_id="genetic_composition_to_landscape",
        from_node="genetic_composition",
        to_node="mutational_landscape",
        description=(
            "Does the resulting genetic composition change the sampled mutational neighborhood?"
        ),
        testable_via="genevra.mechanisms.mutational_landscape.MutationalLandscapeAnalyzer",
    ),
    CausalLink(
        link_id="landscape_to_evolvability",
        from_node="mutational_landscape",
        to_node="future_evolvability",
        description=(
            "Does the mutational landscape's beneficial_fraction predict future evolvability?"
        ),
        testable_via="genevra.mechanisms.robustness.robustness_evolvability_association",
    ),
    CausalLink(
        link_id="evolvability_to_innovation",
        from_node="future_evolvability",
        to_node="innovation",
        description="Does measured evolvability predict subsequent InnovationEvent occurrence?",
        testable_via="genevra.innovation.potential_vs_realized",
    ),
)


@dataclass(frozen=True)
class LinkTestResult:
    link: CausalLink
    status: str
    """'untested', 'association_found', 'no_association_found', or
    'insufficient_data' — never 'confirmed' or 'caused'."""
    evidence: dict[str, Any]
    note: str = (
        "Evidence for one arrow in the causal chain, evaluated independently. This "
        "result says nothing about any other link, and association evidence for "
        "every link in a chain still would not establish the whole chain is causal."
    )


__all__ = ["CausalLink", "CAUSAL_CHAIN", "LinkTestResult"]
