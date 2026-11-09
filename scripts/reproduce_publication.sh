#!/bin/sh
# Verify the frozen GENEVRA reference, then rebuild the manuscript package.
set -eu
if [ "$#" -lt 1 ] || [ "$#" -gt 2 ]; then
    echo "usage: sh scripts/reproduce_publication.sh NEW_OUTPUT [VERIFIED_ARCHIVE]" >&2
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
if [ -n "$archive" ]; then
    sh scripts/reproduce_reference.sh "$output" "$archive"
else
    sh scripts/reproduce_reference.sh "$output"
fi
py="$output/venv/bin/python"
publication=docs/research/phase_28
uv pip install --python "$py" -r "$publication/requirements-publication.txt"
"$py" scripts/build_publication.py "$output/manuscript"
diff -r "$publication/rendered" "$output/manuscript"
echo "GENEVRA manuscript PDF, figures, tables, evidence and receipt reproduced byte for byte."
