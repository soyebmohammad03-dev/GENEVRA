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
