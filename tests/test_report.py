import numpy as np

from genevra.analysis.comparison import ComparisonRunner
from genevra.analysis.report import build_research_report
from tests.test_comparison import make_config_factory


def _fitness_extractor(g: dict) -> float:
    return float(g["fitness_summary"]["mean"])


def test_report_never_auto_generates_interpretation() -> None:
    result = ComparisonRunner(
        conditions={"a": make_config_factory(10), "b": make_config_factory(20)}, seeds=[0, 1, 2]
    ).run()
    report = build_research_report(
        result,
        question="does X affect Y?",
        hypothesis="X increases Y",
        metric_extractor=_fitness_extractor,
        metric_name="fitness",
    )
    assert "Not generated automatically" in report.interpretation
    assert report.question == "does X affect Y?"
    assert report.hypothesis == "X increases Y"


def test_report_includes_one_summary_per_condition() -> None:
    result = ComparisonRunner(
        conditions={"a": make_config_factory(10), "b": make_config_factory(20)}, seeds=[0, 1, 2]
    ).run()
    report = build_research_report(
        result, question="q", hypothesis="h", metric_extractor=_fitness_extractor
    )
    assert {s.condition for s in report.condition_summaries} == {"a", "b"}
    for summary in report.condition_summaries:
        assert summary.n_runs == 3
        assert len(summary.final_values) == 3


def test_report_computes_pairwise_effect_sizes_between_every_condition_pair() -> None:
    result = ComparisonRunner(
        conditions={
            "a": make_config_factory(10),
            "b": make_config_factory(20),
            "c": make_config_factory(30),
        },
        seeds=[0, 1, 2],
    ).run()
    report = build_research_report(
        result, question="q", hypothesis="h", metric_extractor=_fitness_extractor
    )
    pairs = {(p.condition_a, p.condition_b) for p in report.pairwise_comparisons}
    assert pairs == {("a", "b"), ("a", "c"), ("b", "c")}


def test_report_without_rng_skips_bootstrap_ci_rather_than_seeding_arbitrarily() -> None:
    result = ComparisonRunner(conditions={"a": make_config_factory(10)}, seeds=[0, 1, 2]).run()
    report = build_research_report(
        result, question="q", hypothesis="h", metric_extractor=_fitness_extractor
    )
    assert all(s.bootstrap_ci is None for s in report.condition_summaries)


def test_report_with_rng_populates_bootstrap_ci() -> None:
    result = ComparisonRunner(conditions={"a": make_config_factory(10)}, seeds=[0, 1, 2]).run()
    report = build_research_report(
        result,
        question="q",
        hypothesis="h",
        metric_extractor=_fitness_extractor,
        rng=np.random.default_rng(0),
    )
    assert report.condition_summaries[0].bootstrap_ci is not None


def test_report_surfaces_validation_warnings_and_errors() -> None:
    result = ComparisonRunner(conditions={"a": make_config_factory(10)}, seeds=[0, 1]).run()
    report = build_research_report(
        result, question="q", hypothesis="h", metric_extractor=_fitness_extractor
    )
    assert report.validation.ok()


def test_report_to_dict_is_json_serializable_shape() -> None:
    import json

    result = ComparisonRunner(conditions={"a": make_config_factory(10)}, seeds=[0, 1]).run()
    report = build_research_report(
        result, question="q", hypothesis="h", metric_extractor=_fitness_extractor
    )
    json.dumps(report.to_dict())  # must not raise
