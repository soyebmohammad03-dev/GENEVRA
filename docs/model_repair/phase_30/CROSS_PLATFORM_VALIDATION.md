# Cross-platform validation

Run the distribution gate from a checkout with Git and uv. Pass a fresh output directory. The CI workflow runs this gate on Ubuntu 24.04 x86-64 for Python 3.11 and 3.12 and retains installed help and inventory artifacts.

```sh
sh scripts/check_distribution.sh 3.11 NEW_OUTPUT_311
sh scripts/check_distribution.sh 3.12 NEW_OUTPUT_312
```

| Environment | Python | NumPy | Validation |
|---|---|---|---|
| macOS 27.0.1 build 26A434, arm64, uv 0.12.23 | 3.11.17 | 2.4.6 | Core-only wheel and sdist example, resource and dependency checks, 832 wheel tests passed in 160.84 s, no skips, removal verified. |
| macOS 27.0.1 build 26A434, arm64, uv 0.12.23 | 3.12.15 | 2.5.4 | Core-only wheel and sdist example, resource and dependency checks, 832 wheel tests passed in 159.57 s, no skips, removal verified. |
| macOS 27.0.1 build 26A434, arm64, fresh public clone | 3.12.15 | 2.5.4 | Editable install with development and visualization dependencies, 832 tests passed in 151.34 s, no skips. |
| Ubuntu 24.04, x86-64, GitHub-hosted, uv 0.13.7 | 3.11.18 | 2.4.6 | Core-only wheel and sdist example, 832 wheel tests passed in 277.16 s on the final code revision, no skips, removal and frozen hashes verified. |
| Ubuntu 24.04, x86-64, GitHub-hosted, uv 0.13.7 | 3.12.16 | 2.5.4 | Core-only wheel and sdist example, 832 wheel tests passed in 243.34 s on the final code revision, no skips, removal and frozen hashes verified. |

Every platform gate uses a path with spaces and launches the package from outside the source checkout. The tested core environments contain GENEVRA and NumPy. Plotting and test dependencies are installed only after the core example and evidence checks. Each environment compares wheel and sdist JSON bytes and exercises invalid input, missing optional dependencies and package removal.

On the Mac, the seed-zero example across the two Python/NumPy versions differed only in the two recorded version fields. The SHA-256 of its sorted JSON after removing those fields is `2281e3057a3d8af3c8b88ebe67d28981064a3d60048857aae2de6875402a0557`. The [final Ubuntu jobs](https://github.com/soyebmohammad03-dev/GENEVRA/actions/runs/42640941856) retained complete JSON examples and environment receipts. Their version-normalized SHA-256 digests were `2f490fca74b73d39c4b5070427e17a52cc500db428cb25cda5ddfa16012844f3` for Python 3.11 and `c79e95bb9b082ecee3d1ebaaf1cab0af74420c0fdd00673157bb3360559f0ba4` for Python 3.12.

## Numerical portability limit

The example completed 15 generations with 24 final organisms in all four environments. Its final mean fitness was 63.75 on both macOS environments and 75.25 on both Ubuntu environments. A field-by-field comparison of the macOS and Ubuntu Python 3.12 results found 968 differences after ignoring the Python version field, including lineage and trajectory differences. Both used NumPy 2.5.4. The environments also differ in architecture, OS, and Python patch version. This check cannot identify which factor or interaction caused the differences. Within each environment the wheel and sdist produced byte-identical JSON.

Cross-platform installation and execution passed. Cross-platform numerical identity did not hold for this software example. The publication benchmark has its own pinned environment and was not rerun on Linux. Its existing receipts and Phase 30 publication-only rebuild establish only the recorded macOS reproduction scope. Windows was outside the executed matrix.
