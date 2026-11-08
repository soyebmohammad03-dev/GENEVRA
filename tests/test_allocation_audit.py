"""Independent optimization and sensitivity invariants for the GENEVRA audit."""

import json
import math
import runpy
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def audit(monkeypatch):
    monkeypatch.syspath_prepend(str(ROOT / "experiments"))
    monkeypatch.syspath_prepend(str(ROOT))
    return runpy.run_path(str(ROOT / "experiments/allocation_audit.py"))


@pytest.mark.parametrize("budget", [40, 124])
@pytest.mark.parametrize("variances", [None, [0.0002, 0.038], [0.25, 0.25], [0.0, 0.1]])
def test_continuous_neighbor_verifier(audit, budget, variances):
    weights = (0.9, 0.1)

    def loss(high):
        low = budget - 2 * high
        if variances is None:
            return weights[0] / math.sqrt(low) + weights[1] / math.sqrt(high)
        return weights[0] ** 2 * variances[0] / low + weights[1] ** 2 * variances[1] / high

    options = range(1, (budget - 1) // 2 + 1)
    best, worst = min(options, key=loss), max(options, key=loss)
    center = audit["convex_grid_check"](best, budget, (1, 2), weights, variances)
    assert abs(best - center) <= 1
    with pytest.raises(ValueError, match="objective minimum"):
        audit["convex_grid_check"](worst, budget, (1, 2), weights, variances)


def test_sensitivity_keeps_spend_and_width_nested(audit):
    design = json.loads((ROOT / "docs/research/phase_26/design.json").read_text())
    design["replicates"] = 8
    _, cfg = audit["prior"].load_design()
    cell = audit["sensitivity_cell"]
    original = cell(design["base"], design, cfg)
    wide = cell({**design["base"], "width": 0.75}, design, cfg)
    assert original == cell(design["base"], design, cfg)
    for method in original:
        assert wide[method]["useful"] >= original[method]["useful"]
        for key in original[method].keys() - {"useful"}:
            assert wide[method][key] == original[method][key]
        assert original[method]["cost"] == (0 if method == "abstain" else 32768)


def test_pilot_distortion_leaves_fixed_policy_draws_unchanged(audit):
    design = json.loads((ROOT / "docs/research/phase_26/design.json").read_text())
    design["replicates"] = 8
    _, cfg = audit["prior"].load_design()
    base = design["base"]
    a = audit["sensitivity_cell"](base, design, cfg)
    b = audit["sensitivity_cell"]({**base, "pilot_high_scale": 2}, design, cfg)
    assert a["width_proxy"] == b["width_proxy"]
    assert a["equal_spend"] == b["equal_spend"]
    assert b["variance"]["mean_n1"] > a["variance"]["mean_n1"]


def test_invalid_published_raw_rejected_before_verification(audit, tmp_path):
    (tmp_path / "receipt.json").write_text("{}")
    with pytest.raises(ValueError, match="published Phase 25 provenance"):
        audit["reconstruction"](tmp_path)
