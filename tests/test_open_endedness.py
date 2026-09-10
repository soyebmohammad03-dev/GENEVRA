from genevra.analysis.open_endedness import build_open_endedness_report


def make_trajectory(novelty: list[float], diversity: list[float]) -> list[dict]:
    return [
        {
            "generation": i,
            "instantaneous_novelty": n,
            "genotypic_diversity": d,
            "behavioral_diversity": d,
        }
        for i, (n, d) in enumerate(zip(novelty, diversity, strict=True))
    ]


def test_report_never_emits_a_boolean_open_ended_verdict() -> None:
    trajectory = make_trajectory([0.1, 0.2, 0.3, 0.4], [1.0, 1.1, 1.2, 1.3])
    report = build_open_endedness_report(trajectory)
    summary = report.summary()
    assert "open_ended" not in "".join(str(k) for k in summary).lower()
    assert set(summary.keys()) == {
        "novelty_trend",
        "genotypic_diversity_trend",
        "behavioral_diversity_trend",
        "evolvability_trend",
        "stagnation_detected",
        "cumulative_novelty_area",
        "limitation_note",
    }


def test_rising_novelty_trend_is_reported_as_increasing() -> None:
    trajectory = make_trajectory([0.0, 1.0, 2.0, 3.0], [1.0, 1.0, 1.0, 1.0])
    report = build_open_endedness_report(trajectory)
    assert report.novelty_trend.increasing is True
    assert report.novelty_trend.slope > 0.0


def test_declining_novelty_trend_is_reported_as_not_increasing() -> None:
    trajectory = make_trajectory([3.0, 2.0, 1.0, 0.0], [1.0, 1.0, 1.0, 1.0])
    report = build_open_endedness_report(trajectory)
    assert report.novelty_trend.increasing is False
    assert report.novelty_trend.slope < 0.0


def test_evolvability_trend_is_none_when_not_supplied() -> None:
    trajectory = make_trajectory([1.0, 2.0], [1.0, 1.0])
    report = build_open_endedness_report(trajectory)
    assert report.evolvability_trend is None
    assert report.summary()["evolvability_trend"] is None


def test_evolvability_trend_is_populated_when_supplied() -> None:
    trajectory = make_trajectory([1.0, 2.0, 3.0], [1.0, 1.0, 1.0])
    report = build_open_endedness_report(trajectory, evolvability_trend_values=[0.5, 0.6, 0.7])
    assert report.evolvability_trend is not None
    assert report.evolvability_trend.increasing is True


def test_limitation_note_present_and_explicit() -> None:
    trajectory = make_trajectory([1.0, 2.0], [1.0, 1.0])
    report = build_open_endedness_report(trajectory)
    assert "not" in report.limitation_note.lower()
    assert "proof" in report.limitation_note.lower()
