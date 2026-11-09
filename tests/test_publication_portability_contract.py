from pathlib import Path
from runpy import run_path

import pytest

compare = run_path(
    str(Path(__file__).resolve().parents[1] / "scripts/compare_baseline_portability.py")
)["numeric_differences"]


def test_continuous_difference_is_reported_without_rounding():
    assert list(compare({"width": 1.0}, {"width": 1.25})) == [(("width",), 0.25)]


def test_discrete_difference_is_rejected():
    with pytest.raises(ValueError, match="different discrete values"):
        list(compare({"count": 3}, {"count": 4}))


def test_missing_and_nonfinite_values_are_rejected():
    with pytest.raises(ValueError, match="different fields"):
        list(compare({"width": 1.0}, {}))
    with pytest.raises(ValueError, match="non-finite"):
        list(compare({"width": float("nan")}, {"width": 1.0}))
