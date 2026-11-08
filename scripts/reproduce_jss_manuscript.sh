#!/bin/sh
# Assemble and compile the JSS draft without running a benchmark.
set -eu
if [ "$#" -ne 1 ]; then
    echo "usage: sh scripts/reproduce_jss_manuscript.sh NEW_OUTPUT" >&2
    exit 2
fi
case "$1" in
    /*) output=$1 ;;
    *) output=$PWD/$1 ;;
esac
root=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
cd "$root"
phase=docs/research/phase_29
draft=$phase/jss
python=${PYTHON:-python3}
(cd "$phase" && shasum -a 256 -c SHA256SUMS)
(cd docs/research/phase_28 && shasum -a 256 -c SHA256SUMS)
mkdir "$output"
"$python" scripts/build_jss_manuscript.py "$output/manuscript.tex"
cmp "$draft/manuscript.tex" "$output/manuscript.tex"
cp "$draft/references.bib" "$output/"
mkdir "$output/figures"
cp docs/research/phase_28/rendered/figures/*.png "$output/figures/"
if [ -n "${JSS_TEMPLATE_ZIP:-}" ]; then
    cp "$JSS_TEMPLATE_ZIP" "$output/template.zip"
else
    curl -fsSL https://www.jstatsoft.org/public/journals/1/jss-article-tex.zip \
        -o "$output/template.zip"
fi
cd "$output"
printf '%s  template.zip\n' 40cf0004a961d53e0d66c0490f8313dbb07a0699b714b6f13cca2783a1baa274 |
    shasum -a 256 -c -
unzip -q template.zip jss.cls jss.bst jsslogo.jpg
export SOURCE_DATE_EPOCH=1767225600 FORCE_SOURCE_DATE=1
pdflatex --version | sed -n '1p'
for pass in 1 2 3 4; do
    if ! pdflatex -interaction=nonstopmode -halt-on-error manuscript.tex > "pass-$pass.log"; then
        tail -35 "pass-$pass.log" >&2
        exit 1
    fi
    if [ "$pass" -eq 1 ]; then
        bibtex manuscript
    fi
done
if grep -E 'There were undefined|Label\(s\) may have changed|Overfull' manuscript.log; then
    echo "unresolved LaTeX references or overflowing material" >&2
    exit 1
fi
if [ "$(grep -c '^\\bibitem' manuscript.bbl)" -ne 12 ]; then
    echo "compiled bibliography count differs from the twelve verified references" >&2
    exit 1
fi
shasum -a 256 manuscript.tex references.bib manuscript.pdf
