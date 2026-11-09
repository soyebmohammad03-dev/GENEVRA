#!/bin/sh
# Verify frozen research and reproduce the publication candidate in a fresh directory.
set -eu
if [ "$#" -ne 2 ]; then
    echo "usage: sh scripts/verify_publication_candidate.sh {render|replay} NEW_OUTPUT" >&2
    exit 2
fi
case "$1" in
    render|replay) mode=$1 ;;
    *) echo "unknown mode: $1" >&2; exit 2 ;;
esac
case "$2" in
    /*) output=$2 ;;
    *) output=$PWD/$2 ;;
esac
root=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
cd "$root"
phase=docs/model_repair/phase_31
(cd "$phase" && shasum -a 256 -c SHA256SUMS)
mkdir "$output"
{
    git rev-parse HEAD
    uname -a
    uv --version
    pdflatex --version
    bibtex --version
} > "$output/environment.txt"
if [ "$mode" = render ]; then
    sh scripts/reproduce_final_research.sh --publication-only "$output/research"         > "$output/research.log" 2>&1
else
    sh scripts/reproduce_final_research.sh "$output/research" > "$output/research.log" 2>&1
fi
PYTHON="$output/research/venv/bin/python" sh scripts/reproduce_jss_manuscript.sh "$output/jss"     > "$output/jss.log" 2>&1
cmp docs/research/phase_29/jss/manuscript.pdf "$output/jss/manuscript.pdf"
(cd "$output" && shasum -a 256 research/final/audit-receipt.json jss/manuscript.pdf > SHA256SUMS)
echo "Candidate outputs match the frozen artifacts. Logs and hashes are in $output"
