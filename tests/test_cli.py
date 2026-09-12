import json

from genevra.cli import main


def test_run_command_produces_a_result_file(tmp_path) -> None:
    output_path = tmp_path / "result.json"
    exit_code = main(["run", "--seed", "0", "--output", str(output_path)])
    assert exit_code == 0
    with open(output_path) as f:
        data = json.load(f)
    assert data["status"] == "completed"
    assert data["seed"] == 0


def test_run_command_is_deterministic_given_same_seed(tmp_path) -> None:
    path_a = tmp_path / "a.json"
    path_b = tmp_path / "b.json"
    main(["run", "--seed", "1", "--output", str(path_a)])
    main(["run", "--seed", "1", "--output", str(path_b)])
    assert path_a.read_text() == path_b.read_text()


def test_inspect_command_prints_summary(tmp_path, capsys) -> None:
    output_path = tmp_path / "result.json"
    main(["run", "--seed", "0", "--output", str(output_path)])
    exit_code = main(["inspect", str(output_path)])
    assert exit_code == 0
    captured = capsys.readouterr()
    assert "status=completed" in captured.out
    assert "final_fitness_mean=" in captured.out


def test_analyze_command_reports_stagnation_without_conflating_fitness(tmp_path, capsys) -> None:
    output_path = tmp_path / "result.json"
    main(["run", "--seed", "0", "--output", str(output_path)])
    exit_code = main(["analyze", str(output_path)])
    assert exit_code == 0
    captured = capsys.readouterr()
    assert "stagnation_score=" in captured.out
    assert "NOT counted toward stagnation_score" in captured.out


def test_compare_command_lists_controlled_experiments(capsys) -> None:
    exit_code = main(["compare"])
    assert exit_code == 0
    captured = capsys.readouterr()
    assert "exp1_isolated_vs_shared.py" in captured.out


def test_parser_requires_a_subcommand() -> None:
    import pytest

    with pytest.raises(SystemExit):
        main([])


def _write_results(dir_path, seeds) -> None:
    for seed in seeds:
        main(["run", "--seed", str(seed), "--output", str(dir_path / f"seed{seed}.json")])


def test_discover_command_prints_a_report(tmp_path, capsys) -> None:
    results_dir = tmp_path / "results"
    results_dir.mkdir()
    _write_results(results_dir, [0, 1, 2, 3])
    exit_code = main(["discover", str(results_dir)])
    assert exit_code == 0
    captured = capsys.readouterr()
    assert "GENEVRA Discovery Report" in captured.out
    assert "Limitations" in captured.out


def test_discover_command_writes_json_output(tmp_path) -> None:
    results_dir = tmp_path / "results"
    results_dir.mkdir()
    _write_results(results_dir, [0, 1, 2, 3])
    output_path = tmp_path / "report.json"
    exit_code = main(["discover", str(results_dir), "--output", str(output_path)])
    assert exit_code == 0
    with open(output_path) as f:
        data = json.load(f)
    assert "candidate_hypotheses" in data
    assert "limitations" in data


def test_hypothesis_command_runs_without_error(tmp_path, capsys) -> None:
    results_dir = tmp_path / "results"
    results_dir.mkdir()
    _write_results(results_dir, [0, 1, 2])
    exit_code = main(["hypothesis", str(results_dir)])
    assert exit_code == 0


def test_replicate_command_compares_two_result_sets(tmp_path, capsys) -> None:
    original_dir = tmp_path / "original"
    replication_dir = tmp_path / "replication"
    original_dir.mkdir()
    replication_dir.mkdir()
    _write_results(original_dir, [0, 1, 2])
    _write_results(replication_dir, [10, 11, 12])
    exit_code = main(
        [
            "replicate",
            str(original_dir),
            str(replication_dir),
            "--hypothesis-id",
            "h1",
            "--dependent-variable",
            "fitness_summary.mean",
        ]
    )
    assert exit_code == 0
    captured = capsys.readouterr()
    assert "hypothesis_id=h1" in captured.out
    assert "replicated=" in captured.out


def test_literature_command_lists_cases(capsys) -> None:
    exit_code = main(["literature"])
    assert exit_code == 0
    captured = capsys.readouterr()
    assert "case_a" in captured.out
    assert "case_d" in captured.out


def test_literature_command_writes_json_output(tmp_path) -> None:
    output_path = tmp_path / "cases.json"
    exit_code = main(["literature", "--output", str(output_path)])
    assert exit_code == 0
    with open(output_path) as f:
        data = json.load(f)
    assert len(data) == 4
    assert {"case_id", "claim", "spec"} <= data[0].keys()


def test_reproduce_command_runs_a_case_end_to_end(capsys) -> None:
    exit_code = main(
        ["reproduce", "case_a", "--population-size", "4", "--generations", "2", "--seeds", "4"]
    )
    assert exit_code == 0
    captured = capsys.readouterr()
    assert "Literature Reproduction Report" in captured.out
    assert "qualitative pattern" in captured.out.lower()


def test_reproduce_command_writes_json_output(tmp_path) -> None:
    output_path = tmp_path / "report.json"
    exit_code = main(
        [
            "reproduce",
            "case_b",
            "--population-size",
            "4",
            "--generations",
            "2",
            "--seeds",
            "4",
            "--output",
            str(output_path),
        ]
    )
    assert exit_code == 0
    with open(output_path) as f:
        data = json.load(f)
    assert data["result"]["label"] in (
        "SUPPORTED",
        "PARTIALLY_SUPPORTED",
        "NOT_SUPPORTED",
        "CONTRADICTED",
        "INCONCLUSIVE",
        "INVALID_EXPERIMENT",
    )


def test_reproduce_command_rejects_unknown_case() -> None:
    import pytest

    with pytest.raises(SystemExit):
        main(["reproduce", "not_a_case"])


def test_falsify_command_prints_hypotheses(capsys) -> None:
    exit_code = main(["falsify", "plasticity", "novelty"])
    assert exit_code == 0
    captured = capsys.readouterr()
    assert "plasticity itself contributes to novelty" in captured.out


def test_falsify_command_writes_json_output(tmp_path) -> None:
    output_path = tmp_path / "falsify.json"
    exit_code = main(["falsify", "plasticity", "novelty", "--output", str(output_path)])
    assert exit_code == 0
    with open(output_path) as f:
        data = json.load(f)
    assert len(data["hypotheses"]) == len(data["proposed_experiments"])


def test_open_endedness_command_prints_report(tmp_path, capsys) -> None:
    output_path = tmp_path / "result.json"
    main(["run", "--seed", "0", "--output", str(output_path)])
    exit_code = main(["open-endedness", str(output_path)])
    assert exit_code == 0
    captured = capsys.readouterr()
    assert "Open-Endedness Lab Report" in captured.out
    assert "NOT declared 'fully open-ended'" in captured.out


def test_innovation_command_prints_events(tmp_path, capsys) -> None:
    output_path = tmp_path / "result.json"
    main(["run", "--seed", "0", "--output", str(output_path)])
    exit_code = main(["innovation", str(output_path)])
    assert exit_code == 0
    captured = capsys.readouterr()
    assert "innovation event(s) detected" in captured.out


def test_activity_command_prints_summary(tmp_path, capsys) -> None:
    output_path = tmp_path / "result.json"
    main(["run", "--seed", "0", "--output", str(output_path)])
    exit_code = main(["activity", str(output_path)])
    assert exit_code == 0
    captured = capsys.readouterr()
    assert "lineage_persistence=" in captured.out


def test_robustness_command_prints_dimensions(capsys) -> None:
    exit_code = main(["robustness", "--seed", "0", "--num-samples", "2"])
    assert exit_code == 0
    captured = capsys.readouterr()
    assert "genetic: mean=" in captured.out
    assert "behavioral: mean=" in captured.out


def test_robustness_command_writes_json_output(tmp_path) -> None:
    output_path = tmp_path / "robustness.json"
    exit_code = main(
        ["robustness", "--seed", "0", "--num-samples", "2", "--output", str(output_path)]
    )
    assert exit_code == 0
    data = json.loads(output_path.read_text())
    assert "genetic" in data


def test_generalization_command_prints_categories(capsys) -> None:
    exit_code = main(["generalization", "--seed", "0"])
    assert exit_code == 0
    captured = capsys.readouterr()
    assert "train_fitness=" in captured.out
    assert "recurrent:" in captured.out


def test_analyze_mechanisms_command_prints_report(capsys) -> None:
    exit_code = main(["analyze-mechanisms", "--seed", "0", "--num-samples", "2"])
    assert exit_code == 0
    captured = capsys.readouterr()
    assert "Evolutionary Mechanisms Report" in captured.out
    assert "Scientific Note" in captured.out


def test_figures_command_writes_expected_files(tmp_path) -> None:
    result_path = tmp_path / "result.json"
    main(["run", "--seed", "0", "--output", str(result_path)])
    figures_dir = tmp_path / "figures"
    exit_code = main(["figures", str(result_path), "--output-dir", str(figures_dir)])
    assert exit_code == 0
    assert (figures_dir / "fitness_trajectory.png").exists()
    assert (figures_dir / "overview_panel.png").exists()


def test_tables_command_writes_csv_and_markdown(tmp_path) -> None:
    result_path = tmp_path / "result.json"
    main(["run", "--seed", "0", "--output", str(result_path)])
    tables_dir = tmp_path / "tables"
    exit_code = main(["tables", str(result_path), "--output-dir", str(tables_dir)])
    assert exit_code == 0
    assert (tables_dir / "experiment_summary.csv").exists()
    assert (tables_dir / "experiment_summary.md").exists()


def test_artifacts_command_writes_full_tree(tmp_path) -> None:
    result_path = tmp_path / "result.json"
    main(["run", "--seed", "0", "--output", str(result_path)])
    artifact_root = tmp_path / "research_artifacts"
    exit_code = main(["artifacts", str(result_path), "--output-root", str(artifact_root)])
    assert exit_code == 0
    experiment_dirs = list(artifact_root.iterdir())
    assert len(experiment_dirs) == 1
    assert (experiment_dirs[0] / "reports" / "report.md").exists()
    assert (experiment_dirs[0] / "provenance" / "provenance.json").exists()


def test_report_command_prints_text_by_default(tmp_path, capsys) -> None:
    result_path = tmp_path / "result.json"
    main(["run", "--seed", "0", "--output", str(result_path)])
    exit_code = main(
        ["report", str(result_path), "--output-root", str(tmp_path / "research_artifacts")]
    )
    assert exit_code == 0
    captured = capsys.readouterr()
    assert "Scientific-Language Safeguards" in captured.out


def test_report_command_writes_json_output(tmp_path) -> None:
    result_path = tmp_path / "result.json"
    main(["run", "--seed", "0", "--output", str(result_path)])
    report_path = tmp_path / "report.json"
    exit_code = main(
        [
            "report",
            str(result_path),
            "--output-root",
            str(tmp_path / "research_artifacts"),
            "--output",
            str(report_path),
        ]
    )
    assert exit_code == 0
    data = json.loads(report_path.read_text())
    assert data["seeds"] == [0]
