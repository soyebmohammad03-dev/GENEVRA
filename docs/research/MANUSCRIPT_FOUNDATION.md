# Manuscript foundation

**Working title** — When calibration cannot see the target: a reproducible stress test of sampling-frame blindness and certification.

## Abstract

Calibration precision can improve while a population target remains unidentified. GENEVRA's frozen synthetic benchmarks separate tail calibration, frame coverage, and certification decisions. At matched acquisition access, the combined audit detected single-stream staleness but issued 180 false certificates in 512 shared-blind runs. A coverage envelope restored coverage in a planted omission case when external bounds held, at the cost of precision. A budgeted worst-case width planner performed worse than equal spend for the frozen rare-event design. The artifact supports independent reconstruction of these negative feasibility findings. Real-world target access, reference outcomes and procurement costs remain unverified.

## Introduction, gap and related work

Introduce paired-score measurement and the distinction between precision and identification. Survey sampling and partial-identification work establish the core limitations. Predictive calibration and selective inference address different risks under their sampling assumptions. The narrow gap is a reproducible assay-level comparison of representative versus shared-blind access, coupled with an explicit cost and coverage-envelope ablation. Use the [verified primary literature and contribution matrix](METHODOLOGY.md) as the reference list and relationship guide.

## Questions and mathematical formulation

1. How does access to tail and support information change achievable confidence width?
2. Can matched-access audits reduce false source-anchor certification without sacrificing useful decisions?
3. When do valid external omission bounds restore coverage, and does worst-case width optimization help at fixed budget?

Present the mixture mean, the anchor discrepancy, reachable and inaccessible mass decomposition and separate scoring endpoints as defined in [methodology](METHODOLOGY.md). State independent units, support, declared loss and role separation explicitly.

## Methods, experiment and statistical analysis

Use the [frozen experiment index](EXPERIMENT_INDEX.md) as the study map. Compare phase-local designs rather than pooling across different laws or estimands. Specify exactly how simulated truth is reserved for scoring. Report Phase 18 paired Hoeffding utility contrasts and simultaneous exact upper risk. Report the extension's paired coverage-with-precision contrast and descriptive secondary intervals, including adverse controls. Follow the distinction among aims, data generation, estimands, methods and performance measures in [Morris, White and Crowther, 2019](https://doi.org/10.1002/sim.8086).

## Results and discussion

Use the notebook's precision and identification-floor panels, the committed extension SVG, and a table of admitted, covered, certified and false outcomes. Show shared blindness alongside single-stream failures. Include the extension primary difference of −85.94 percentage points and interval [−97.94, −73.93]. Do not interpret failure to establish superiority in Phase 18 as equivalence. The planner optimizes a conservative proxy and sacrificed information from the high-event stratum in this design.

## Limitations and conclusion

The experiments use planted failures, synthetic or model-specific endpoints, stipulated costs, supplied conditional access and assumption-conditional external bounds. No external reviewer, empirical or biological validation is established. The manuscript remains a foundation. The smallest credible additional evidence is a third-party artifact reconstruction and one independently specified held-out comparison with documented access, measured costs and defensible external omission bounds. A biological claim requires independently adjudicated outcomes and a validated endpoint bridge. Retain the technical artifact if the external comparison cannot be justified.

## Supplement

Include the immutable archive, provenance, configuration, raw sufficient observations, independent reconstruction, full result tables, decision definitions and explicit negative cases.
