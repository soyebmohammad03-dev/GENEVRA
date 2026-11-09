#!/bin/sh
# Build the editorial candidate using the verified Phase 29 typesetting inputs.
set -eu
if [ "$#" -ne 1 ]; then
    echo "usage: sh scripts/reproduce_editorial_manuscript.sh NEW_OUTPUT" >&2
    exit 2
fi
case "$1" in
    /*) output=$1 ;;
    *) output=$PWD/$1 ;;
esac
root=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
cd "$root"
sh scripts/reproduce_jss_manuscript.sh "$output"
cp docs/model_repair/FINAL_CLOSURE/EDITORIAL_AUDIT/manuscript.tex "$output/manuscript.tex"
cd "$output"
export SOURCE_DATE_EPOCH=1767225600 FORCE_SOURCE_DATE=1
for pass in 1 2 3; do
    if ! pdflatex -interaction=nonstopmode -halt-on-error manuscript.tex > "editorial-$pass.log"; then
        tail -35 "editorial-$pass.log" >&2
        exit 1
    fi
    if [ "$pass" -eq 1 ]; then
        bibtex manuscript
    fi
done
if grep -E 'There were undefined|Label\(s\) may have changed|Overfull' manuscript.log; then
    exit 1
fi
test "$(grep -c '^\\bibitem' manuscript.bbl)" -eq 12
shasum -a 256 manuscript.tex references.bib manuscript.pdf
