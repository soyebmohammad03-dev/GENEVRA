#!/bin/sh
# Exercise both distributions outside the checkout using isolated environments.
set -eu
if [ "$#" -ne 2 ]; then
    echo "usage: sh scripts/check_distribution.sh PYTHON_VERSION NEW_OUTPUT" >&2
    exit 2
fi
case "$2" in
    /*) output=$2 ;;
    *) output=$PWD/$2 ;;
esac
root=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
mkdir "$output"
output=$(CDPATH= cd -- "$output" && pwd -P)
cd "$root"
uv build --out-dir "$output/dist"
set -- "$1" "$output"/dist/*.whl
wheel=$2
uv venv --python "$1" "$output/wheel"
uv venv --python "$1" "$output/source"
p="$output/wheel/bin/python"
cli="$output/wheel/bin/genevra"
s="$output/source/bin/python"
uv pip install --python "$p" "$wheel"
uv pip check --python "$p"
uv pip install --python "$s" "$output"/dist/*.tar.gz
uv pip check --python "$s"
mkdir "$output/outside checkout"
cd "$output/outside checkout"
# An unrelated repository must never become the source of wheel provenance.
git init -q
git -c user.name=Test -c user.email=test@example.invalid commit --allow-empty -qm fixture
"$p" -I -c 'import importlib.metadata as m; print(m.version("genevra")); assert {d.metadata["Name"].lower() for d in m.distributions()} == {"genevra", "numpy"}'
"$cli" run --seed 0 --output 'wheel result.json'
"$cli" inspect 'wheel result.json'
"$cli" analyze 'wheel result.json'
"$output/source/bin/genevra" run --seed 0 --output 'sdist result.json'
cmp 'wheel result.json' 'sdist result.json'
"$p" -c 'import hashlib; from pathlib import Path; print("Baseline JSON SHA-256", hashlib.sha256(Path("wheel result.json").read_bytes()).hexdigest())'
if "$cli" run --seed invalid > invalid.log 2>&1; then
    echo "accepted an invalid seed" >&2
    exit 1
fi
grep 'invalid int value' invalid.log
if "$cli" figures 'wheel result.json' --output-dir figures > missing-viz.log 2>&1; then
    echo "figures ran without optional plotting dependencies" >&2
    exit 1
fi
grep 'Run pip install matplotlib' missing-viz.log
"$cli" verify-evidence "$root/research_evidence" --output evidence.json
uv pip install --python "$p" "$wheel[viz]"
uv pip check --python "$p"
"$p" -I "$root/scripts/check_distribution.py" "$wheel" "$root" "$output/distribution.json"
uv pip install --python "$p" pytest
MPLBACKEND=Agg "$p" -I -m pytest -o "cache_dir=$output/pytest-cache" "$root/tests"
uv pip uninstall --python "$p" genevra
test ! -e "$cli"
"$p" -I -c 'import importlib.util; assert importlib.util.find_spec("genevra") is None'
