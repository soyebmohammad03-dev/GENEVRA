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
| Ubuntu 24.04, x86-64, GitHub-hosted, uv 0.13.7 | 3.11.18 | 2.4.6 | Core-only wheel and sdist example, 832 wheel tests passed in 101.00 s, no skips, removal and frozen hashes verified. |
| Ubuntu 24.04, x86-64, GitHub-hosted | 3.12 | See CI dependency log | The [Ubuntu matrix record](https://github.com/soyebmohammad03-dev/GENEVRA/actions/runs/42640162600) records the resolved version and result. |

Every platform gate uses a path with spaces and launches the package from outside the source checkout. The tested core environments contain GENEVRA and NumPy. Plotting and test dependencies are installed only after the core example and evidence checks. Each environment compares wheel and sdist JSON bytes and exercises invalid input, missing optional dependencies and package removal.

On the Mac, the seed-zero example across the two Python/NumPy versions differed only in the two recorded version fields. The SHA-256 of its sorted JSON after removing those fields is `2281e3057a3d8af3c8b88ebe67d28981064a3d60048857aae2de6875402a0557`. The Linux job also records the raw and version-normalized JSON fingerprints and retains the example for comparison. These are checks on one software example and its environments. They do not establish cross-platform exactness of the publication benchmark. Windows was outside the executed matrix.
