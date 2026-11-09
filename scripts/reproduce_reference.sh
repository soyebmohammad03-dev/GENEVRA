#!/bin/sh
# Reproduce GENEVRA using a new output directory and a pinned local interpreter.
set -eu
if [ "$#" -lt 1 ] || [ "$#" -gt 2 ]; then
    echo "usage: sh scripts/reproduce_reference.sh NEW_OUTPUT [VERIFIED_ARCHIVE]" >&2
    exit 2
fi
case "$1" in
    /*) output=$1 ;;
    *) output=$PWD/$1 ;;
esac
archive=${2-}
case "$archive" in
    /*|'') ;;
    *) archive=$PWD/$archive ;;
esac
root=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
cd "$root"
mkdir "$output"
uv venv --python 3.12.15 "$output/venv"
py="$output/venv/bin/python"
uv pip install --python "$py" -r docs/research/phase_23/requirements-macos-arm64.txt
if [ -n "$archive" ]; then
    "$py" scripts/benchmark_challenge.py reproduce --archive "$archive" --output "$output/replay"
else
    "$py" scripts/benchmark_challenge.py reproduce --output "$output/replay"
fi
PYTHONPATH=src "$py" experiments/allocation_challenge.py --output "$output/phase25"
for file in receipt.json results.json contrasts.csv allocation.svg; do
    cmp "docs/research/phase_25/$file" "$output/phase25/$file"
done
"$py" scripts/benchmark_reference.py --phase25-raw "$output/phase25/raw.csv" \
    --replay "$output/replay" --output "$output/reference-verification.json"
cmp docs/research/phase_27/reference-verification.json "$output/reference-verification.json"
echo "GENEVRA frozen replay, figures, and separate reference verification passed."
