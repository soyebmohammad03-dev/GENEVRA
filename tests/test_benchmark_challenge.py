"""Adversarial fixtures for the independent challenge scoring contract."""

import runpy
from pathlib import Path

import pytest


@pytest.fixture(scope="module")
def api(monkeypatch_module):
    directory = Path(__file__).resolve().parents[1] / "scripts"
    monkeypatch_module.syspath_prepend(str(directory))
    return runpy.run_path(str(directory / "benchmark_challenge.py"))


@pytest.fixture(scope="module")
def monkeypatch_module():
    with pytest.MonkeyPatch.context() as patch:
        yield patch


@pytest.mark.parametrize(
    ("interval", "truth", "abstention", "coverage", "false_label"),
    [
        ((0.6, 0.6), 0.6, False, True, False),
        ((0.6, 0.7), 0.6, True, True, False),
        ((0.601, 0.7), 0.6, False, False, True),
        ((-0.6, -0.6), -0.6, False, True, False),
        ((-240.0, 240.0), 0.6, True, True, False),
        ((0.8, 0.9), 1.1, False, False, False),
    ],
)
def test_distinct_interval_endpoints(api, interval, truth, abstention, coverage, false_label):
    result = api["interval_metrics"](*interval, truth, True, 0.31, 0.6, 0.6, 0.3)
    assert (result["abstention"], result["coverage"], result["false_label"]) == (
        abstention,
        coverage,
        false_label,
    )
    assert result["false_certification"]


@pytest.mark.parametrize(
    "interval", [(float("nan"), 0.6), (0.0, float("inf")), (2.0, 1.0), (-241.0, 0.0)]
)
def test_invalid_interval_fails(api, interval):
    with pytest.raises(ValueError, match="interval endpoints"):
        api["interval_metrics"](*interval, 0.0, False, 0.3, 0.6, 0.6, 0.3)


@pytest.mark.parametrize(
    "rows",
    [
        "",
        "a,0,0,1,0\na,0,0,1,0\n",
        "a,-1,0,1,0\n",
        "a,1,0,1,0\n",
        "wrong,0,0,1,0\n",
        "a,0,0,1,True\n",
        "a,0,0,1,0,extra\n",
    ],
)
def test_missing_duplicate_or_invalid_rows_fail(api, tmp_path, rows):
    path = tmp_path / "submission.csv"
    path.write_text("case,replicate,low,high,certificate\n" + rows)
    with pytest.raises(ValueError):
        api["load_submission"](path, {"a": 1})


def test_conditioning_and_undefined_denominator(api, tmp_path):
    path = tmp_path / "submission.csv"
    path.write_text("case,replicate,low,high,certificate\na,1,-240,240,0\na,0,0,.5,0\n")
    rows = api["load_submission"](path, {"a": 2})
    cfg = {"epsilon": 0.6, "width_target": 0.6, "transfer_tolerance": 0.3}
    metrics, utility = api["evaluate"](rows, {"a": (0.3, [0.3, 0.31])}, cfg)
    rates = metrics["a"]["rates"]
    assert rates["coverage"]["n"] == 2
    assert rates["coverage_given_decision"]["n"] == 1
    assert rates["false_among_certified"]["rate"] is None
    assert rates["coverage_given_certificate"]["n"] == 0
    assert utility == {"a": [0, 0]}
    at_tolerance = api["interval_metrics"](0.0, 0.5, 0.3, True, 0.3, 0.6, 0.6, 0.3)
    assert not at_tolerance["false_certification"]


def test_pairing_and_wilson_endpoints(api):
    assert api["paired"]({"a": [1, -1]}, {"a": [-1, 1]}, ["a"], 0.05)["difference"] == 0
    with pytest.raises(ValueError, match="unbalanced"):
        api["paired"]({"a": [1, -1]}, {"a": [-1]}, ["a"], 0.05)
    assert api["rate"](0, 512)["high"] == pytest.approx(0.0074469757228829)
    assert api["rate"](512, 512)["low"] == pytest.approx(0.9925530242771171)


def test_numeric_comparison_absolute_tolerance(api):
    api["compare"](1.0, 1.0 + 5e-10, "roundoff")
    with pytest.raises(ValueError, match="mismatch"):
        api["compare"](1.0, 1.0 + 5e-8, "mismatch")
