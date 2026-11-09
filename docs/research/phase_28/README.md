# GENEVRA publication package

**Status.** Journal manuscript draft for independent review. External reproduction and empirical validation remain outstanding. No submission, peer-review decision or publication is recorded.

- [Rendered manuscript PDF](rendered/GENEVRA-manuscript.pdf) and [source](MANUSCRIPT.md)
- [Bibliography](REFERENCES.md) and [supplementary methods and mathematical appendix](SUPPLEMENT.md)
- [Venue assessment](VENUES.md), [submission templates](SUBMISSION_MATERIALS.md), and [internal adversarial review](REVIEWER_READINESS.md)
- [Evidence extract](rendered/evidence.json), [source and output receipt](rendered/build-receipt.json), and [completion report](PHASE_28_COMPLETION_REPORT.md)
- [Manuscript citation metadata](citation.json), [software citation](../../../CITATION.cff) and [external evaluation protocol](../phase_27/EXTERNAL_PROTOCOL.md)

## Figure and table inventory

| Item | Material | Role |
|---|---|---|
| Figure 1 | [Decision diagnostic](rendered/figures/diagnostic.png) | Conceptual schematic |
| Figure 2 | [Design and reproduction architecture](rendered/figures/design.png) | Conceptual schematic |
| Figure 3 | [Shared-blindness failure and false certification](rendered/figures/shared.png) | Frozen Phase 18 |
| Figure 4 | [Allocation, coverage and width decomposition](rendered/figures/allocation.png) | Frozen Phase 25 and Phase 26 reconstruction |
| Figure 5 | [Useful-precision sensitivity](rendered/figures/sensitivity.png) | Separate exploratory Phase 26 subset |
| Table 1 | [Notation](rendered/tables/notation.csv) | Definitions |
| Table 2 | [Shared-blindness endpoints](rendered/tables/shared.csv) | Frozen Phase 18 |
| Table 3 | [Primary allocation](rendered/tables/allocation.csv) | Frozen Phase 25 and Phase 26 reconstruction |
| Table 4 | [Exploratory sensitivity](rendered/tables/sensitivity.csv) | Separate Phase 26 subset |

Captions in the PDF state the units, denominators and distinction between frozen evidence, exploratory analyses and diagrams. Complete scenario data remain in the linked historical artifacts.

## Build from a clean public checkout

The reference environment is macOS arm64, CPython 3.12.15, uv and the pinned [replay](../phase_23/requirements-macos-arm64.txt) and [publication](requirements-publication.txt) dependencies. Allow 2 GiB for the extracted archive and environment.

```sh
git clone --branch research/publication-development https://github.com/soyebmohammad03-dev/GENEVRA.git
cd GENEVRA
(cd docs/research/phase_28 && shasum -a 256 -c SHA256SUMS)
scratch=$(mktemp -d)
sh scripts/reproduce_publication.sh "$scratch/publication-replay"
```

The command runs Phase 27's clean verification first. An optional second argument points to a verified historical capsule. It then installs the pinned PDF packages, rebuilds all assets from frozen files and compares the full generated directory, including the PDF, byte for byte. The builder uses Matplotlib's bundled DejaVu fonts and ReportLab's invariant mode. Use the pinned reference platform for byte comparisons. For cross-platform review report any rendering differences alongside numerical agreement. The generated files are versioned here and the rendered PDF is a draft for review.
