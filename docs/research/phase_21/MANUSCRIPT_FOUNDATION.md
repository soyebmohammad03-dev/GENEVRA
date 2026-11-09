# Phase 21 manuscript foundation

## Working title

When independent calibration shares a blind spot: a matched-access benchmark and an external validation protocol.

## Abstract

Calibration precision and target representativeness are distinct. We assemble a reproducible benchmark for population-mean confidence and source-anchor certification under matched access. In a frozen synthetic shared-blind condition, the combined audit had zero mean coverage and issued 180 false certificates in 512 runs. A partial-identification envelope restored coverage under valid supplied bounds in a separate synthetic condition, but the cost-constrained width proxy reduced realized precision. We reconstruct U.S. Census Demographic Analysis coverage estimates as a public-data diagnostic of reference sensitivity. They are aggregate estimates and cannot validate the certificate. We specify a prospective study with independent target enumeration, blinded reference measurement and matched acquisition costs. No field operating characteristics have been measured.

## Introduction, related work and gap

Survey coverage error and selection bias can persist when distinct collection channels miss the same target units. Existing partial-identification theory explains why the missing outcomes cannot be recovered from agreement. The [literature matrix](LITERATURE_AND_NOVELTY.md) positions the benchmark against bounded selection, sample-constrained inference, multiple-frame estimation, covariate-shift conformal prediction, and held-out risk control. The gap is operational and empirical. A reproducible evaluation has to align information, cost, target and certificate loss while retaining refusal as an outcome.

## Question and mathematical formulation

Can an omission-aware policy increase useful correct certificates at matched cost while controlling adverse certification against an independently enumerated target? Let p=(1−m)r+mz, with reachable event rate r, inaccessible target mass m and hidden event rate z. The vertex hull is exact for rectangular input restrictions. Confidence statements require valid reachable bands and external evidence on m and z. Define target theta and an acquisition-only anchor a. An issued certificate claims |theta−a|≤delta. Mean coverage, certainty about anchor error, and threshold resolution are separate endpoints.

## Completed evidence

Use Phase 18 and the Phase 19 extension as frozen synthetic results. Report one-stream versus shared-blind cases, paired matched-access utility, width and refusal. Report the adverse external-bound controls. The Phase 21 diagnostic reproduces DA series −5.3%, −5.4%, −5.5%, and a separate 2024 national net error of −5.46% from source counts. It illustrates the dependence of an estimate on the reference construction. It does not supply GENEVRA labels, a missing-mass bound or field policy evidence.

## Proposed methodology and comparison

The [external protocol](EXTERNAL_VALIDATION_PROTOCOL.md) specifies a full-frame probability reference, separate acquisition and blind laboratory adjudication, retaining inaccessible and unresolved units. The [comparison protocol](FAIR_COMPARISON_PROTOCOL.md) freezes equal-access regimes, explicit costs, baseline eligibility and adverse and useful-certificate outcomes. A feasibility pilot precedes confirmation. Region, endpoint, sampling and consent or release conditions remain to be registered with an independent partner. No policy result is inferred from the proposed design.

## Discussion, limitations and conclusion

The project-specific contribution is an audit-ready benchmark and negative feasibility findings. Established probability and partial identification explain the observed failures. The external diagnostic illustrates the value and limits of a separately constructed reference. A matched-access field comparison still requires a credible target roster, independently adjudicated outcomes and measured costs. If those cannot be obtained, the technical artifact remains the defensible scope. Biological validity needs an independent endpoint bridge and separate experiments.

## Reproducibility and references

The [review package](REPRODUCIBILITY.md) contains the pinned sources, independent calculation instructions, figure and expected results. The [frozen Phase 20 archive](../README.md) reconstructs prior synthetic results. Use [source and access citations](DATASET_ASSESSMENT.md) for datasets and the [primary literature matrix](LITERATURE_AND_NOVELTY.md) for statistical attribution. No external reviewer endorsement is asserted.
