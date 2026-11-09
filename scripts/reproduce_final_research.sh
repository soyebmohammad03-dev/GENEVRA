#!/bin/sh
# Reproduce the frozen benchmark and final GENEVRA manuscript.
set -eu
publication_only=false
if [ "${1-}" = "--publication-only" ]; then
    publication_only=true
    shift
fi
if [ "$#" -lt 1 ] || [ "$#" -gt 2 ]; then
    echo "usage: sh scripts/reproduce_final_research.sh [--publication-only] NEW_OUTPUT [VERIFIED_ARCHIVE]" >&2
    exit 2
fi
case "$1" in
    /*) output=$1 ;;
    *) output=$PWD/$1 ;;
esac
archive=${2-}
if [ "$publication_only" = true ] && [ "$#" -ne 1 ]; then
    echo "--publication-only needs only a new output path" >&2
    exit 2
fi
case "$archive" in
    /*|'') ;;
    *) archive=$PWD/$archive ;;
esac
root=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
cd "$root"
publication=docs/research/phase_29
echo "Checking frozen evidence"
shasum -a 256 -c "$publication/FROZEN_SHA256SUMS"
if [ "$publication_only" = true ]; then
    echo "Verifying and rendering existing publication evidence"
    (cd docs/research/phase_28 && shasum -a 256 -c SHA256SUMS)
    (cd "$publication" && shasum -a 256 -c SHA256SUMS)
    mkdir "$output"
    uv venv --python 3.12.15 "$output/venv"
    uv pip install --python "$output/venv/bin/python" \
        -r docs/research/phase_23/requirements-macos-arm64.txt \
        -r docs/research/phase_28/requirements-publication.txt
    "$output/venv/bin/python" scripts/final_research_audit.py "$output/final"
    diff -r "$publication/rendered" "$output/final"
    echo "GENEVRA final manuscript and audit receipt reproduced byte for byte from frozen results."
    exit 0
fi
echo "Replaying frozen reference and publication inputs"
if [ -n "$archive" ]; then
    sh scripts/reproduce_publication.sh "$output" "$archive"
else
    sh scripts/reproduce_publication.sh "$output"
fi
echo "Checking primary widths and rendering final manuscript"
"$output/venv/bin/python" scripts/final_research_audit.py "$output" "$output/final"
diff -r "$publication/rendered" "$output/final"
echo "GENEVRA final manuscript and audit receipt reproduced byte for byte."
