import pytest

from genevra.discovery.multiple_testing import benjamini_hochberg


def test_all_significant_p_values_stay_significant_under_bh() -> None:
    results = benjamini_hochberg([0.001, 0.002, 0.003], alpha=0.05)
    assert all(r.significant for r in results)


def test_bh_rejects_fewer_findings_than_uncorrected_threshold() -> None:
    p_values = [0.01, 0.02, 0.03, 0.04, 0.20, 0.50, 0.80, 0.90]
    results = benjamini_hochberg(p_values, alpha=0.05)
    uncorrected_significant = sum(1 for p in p_values if p < 0.05)
    corrected_significant = sum(1 for r in results if r.significant)
    assert corrected_significant <= uncorrected_significant


def test_labels_reflect_is_primary_flag() -> None:
    results = benjamini_hochberg([0.01, 0.02], is_primary=[True, False])
    assert results[0].label == "confirmatory"
    assert results[1].label == "exploratory"


def test_q_values_are_monotone_with_sorted_p_values() -> None:
    p_values = [0.5, 0.01, 0.3, 0.04]
    results = benjamini_hochberg(p_values)
    order = sorted(range(len(p_values)), key=lambda i: p_values[i])
    q_in_order = [results[i].q_value for i in order]
    assert q_in_order == sorted(q_in_order)


def test_rejects_mismatched_is_primary_length() -> None:
    with pytest.raises(ValueError):
        benjamini_hochberg([0.01, 0.02], is_primary=[True])


def test_empty_input_returns_empty_list() -> None:
    assert benjamini_hochberg([]) == []
