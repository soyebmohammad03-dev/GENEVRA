# Independent verification

The verifier imports no GENEVRA code. It uses vectorized long-double likelihood-ratio inversion instead of scalar KL inversion, closed-form missing-mass endpoints instead of vertex enumeration, and a separate vectorized exhaustive budget search. It checks the raw scenario and seed namespaces, prefix nesting, paid rows and latent denominators, interval widths, all 630 counts and Wilson intervals, and the paired primary contrast. Floating comparisons use absolute 1e-9 and zero relative tolerance. Counts and decision flags agree exactly. Verified 18 cells and 9,216 paired synthetic replicates. No discrepancy exceeded tolerance.

The production runner regenerated both raw and result files byte for byte in a fresh environment. The exact invocation is in the reproduction guide. This is local numerical verification, without external peer review. Structural seed checks establish separation in the declared generator, not population independence outside it.
