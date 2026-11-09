# Wheel compatibility report

The previous 829-test wheel run failed 26 tests. All stack traces are accounted for below. The missing paths were computed relative to installed modules, so the loader searched inside the Python environment for the repository-level `experiments/` directory. The CLI entry point itself was present.

| Previous failing test | First missing file | Entry path |
|---|---|---|
| `tests/test_cli.py::test_run_command_produces_a_result_file` | `baseline.py` | CLI baseline configuration, directly or via a result fixture |
| `tests/test_cli.py::test_run_command_is_deterministic_given_same_seed` | `baseline.py` | CLI baseline configuration, directly or via a result fixture |
| `tests/test_cli.py::test_inspect_command_prints_summary` | `baseline.py` | CLI baseline configuration, directly or via a result fixture |
| `tests/test_cli.py::test_analyze_command_reports_stagnation_without_conflating_fitness` | `baseline.py` | CLI baseline configuration, directly or via a result fixture |
| `tests/test_cli.py::test_discover_command_prints_a_report` | `baseline.py` | CLI baseline configuration, directly or via a result fixture |
| `tests/test_cli.py::test_discover_command_writes_json_output` | `baseline.py` | CLI baseline configuration, directly or via a result fixture |
| `tests/test_cli.py::test_hypothesis_command_runs_without_error` | `baseline.py` | CLI baseline configuration, directly or via a result fixture |
| `tests/test_cli.py::test_replicate_command_compares_two_result_sets` | `baseline.py` | CLI baseline configuration, directly or via a result fixture |
| `tests/test_cli.py::test_open_endedness_command_prints_report` | `baseline.py` | CLI baseline configuration, directly or via a result fixture |
| `tests/test_cli.py::test_innovation_command_prints_events` | `baseline.py` | CLI baseline configuration, directly or via a result fixture |
| `tests/test_cli.py::test_activity_command_prints_summary` | `baseline.py` | CLI baseline configuration, directly or via a result fixture |
| `tests/test_cli.py::test_robustness_command_prints_dimensions` | `baseline.py` | CLI baseline configuration, directly or via a result fixture |
| `tests/test_cli.py::test_robustness_command_writes_json_output` | `baseline.py` | CLI baseline configuration, directly or via a result fixture |
| `tests/test_cli.py::test_generalization_command_prints_categories` | `baseline.py` | CLI baseline configuration, directly or via a result fixture |
| `tests/test_cli.py::test_analyze_mechanisms_command_prints_report` | `baseline.py` | CLI baseline configuration, directly or via a result fixture |
| `tests/test_cli.py::test_figures_command_writes_expected_files` | `baseline.py` | CLI baseline configuration, directly or via a result fixture |
| `tests/test_cli.py::test_tables_command_writes_csv_and_markdown` | `baseline.py` | CLI baseline configuration, directly or via a result fixture |
| `tests/test_cli.py::test_artifacts_command_writes_full_tree` | `baseline.py` | CLI baseline configuration, directly or via a result fixture |
| `tests/test_cli.py::test_report_command_prints_text_by_default` | `baseline.py` | CLI baseline configuration, directly or via a result fixture |
| `tests/test_cli.py::test_report_command_writes_json_output` | `baseline.py` | CLI baseline configuration, directly or via a result fixture |
| `tests/test_cli.py::test_population_analysis_command_prints_summary` | `baseline.py` | CLI baseline configuration, directly or via a result fixture |
| `tests/test_cli.py::test_reproduce_evidence_then_verify_evidence_roundtrip` | `exp1_isolated_vs_shared.py` | Evidence builder through CLI or API |
| `tests/test_evidence.py::TestBuildEvidencePackage::test_quick_scale_produces_verifiable_package` | `exp1_isolated_vs_shared.py` | Evidence builder through CLI or API |
| `tests/test_evidence.py::TestBuildEvidencePackage::test_rq4_confounded_and_rq4b_corrected_both_present` | `exp1_isolated_vs_shared.py` | Evidence builder through CLI or API |
| `tests/test_evidence.py::TestBuildEvidencePackage::test_deterministic_case_a_metric_extraction` | `exp1_isolated_vs_shared.py` | Evidence builder through CLI or API |
| `tests/test_evidence.py::TestBuildEvidencePackage::test_no_research_question_left_not_tested_without_reason` | `exp1_isolated_vs_shared.py` | Evidence builder through CLI or API |

The builder subsequently requires `exp_ecology_corrected.py`. It did not reach that stage in the old failure logs. Both distributions carry all three files verbatim. Wheel loads use `importlib.resources` and a fixed allowlist. Editable installs use the source tree that provided the loaded package. The working directory is irrelevant. The published benchmark and controlled comparison scripts remain checkout workflows.

The checks run the same test suite without exclusions. Plotting and evidence-generation tests install the documented visualization extra. The core-only pass separately verifies install, import, CLI execution, evidence verification and a missing-extra diagnostic.
