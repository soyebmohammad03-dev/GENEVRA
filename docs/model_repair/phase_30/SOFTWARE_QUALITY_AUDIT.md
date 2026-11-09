# Software quality audit

| Area | Review and change |
|---|---|
| Architecture and API | Preserved the simulator, analyzers, configuration and CLI entry point. Consolidated lookup of the three runtime scripts. Source-only comparisons now say where to run them. |
| Input handling | Package-resource lookup accepts three fixed filenames. Tests reject traversal-like names and require an actionable missing-resource diagnostic. The installed CLI checks invalid seeds and explains how to install plotting support. |
| Paths and provenance | Source revision lookup uses the checkout that contains the imported package. A standalone wheel reports revision unavailable, even when launched inside an unrelated Git repository. Record the verified wheel digest separately when tracing an installed run. |
| Determinism | Runtime experiment code is unchanged byte for byte. Seeded JSON agrees between wheel and source distribution under the same environment. The frozen research replay has its own pins and receipts. |
| Dependencies | Runtime declares NumPy. Plotting is an extra. Build, lint, and test tools are separate. Verification records resolved versions rather than claiming compatibility for every permissible dependency version. |
| Security and cleanup | The replay checker verifies archive and member SHA-256 and rejects duplicate and traversal member names before extraction. Resource extraction uses a context manager. The legacy evidence verifier is intended for trusted evidence packages and does not enforce a sandbox for arbitrary user-supplied manifest paths. This phase did not broaden that trust boundary. |
| Test scope | The tracked suite retains units and integrations. Packaging checks use isolated wheel and sdist environments. Frozen evidence checks are separate. The optional plotting test modules use their existing Matplotlib dependency check. |
| Tooling | Ruff lint, Ruff formatting, strict mypy, installed CLI help and dependency inventory checks run without changing test assertions. |
