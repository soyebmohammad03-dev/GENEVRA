# Adversarial test matrix

No benchmark parameter was tuned. Published stochastic results are replays of archived inputs. Scorer fixtures are deterministic and test the contract only.

| Case | Expected from the assumptions | Observed synthetic or deterministic check |
|---|---|---|
| Correct frames | Matching laws make target coverage possible under the declared model | Phase 18 combined covered 512/512 in registered matched case |
| Shared missingness | Agreement can conceal a common target error | Combined 0/512 coverage and 180/512 false certificates |
| Asymmetric missingness | A large discrepancy can flag a mismatch without identifying which channel is right | Phase 18 combined abstained 512/512 in both stale cases |
| Valid omitted-mass cap | Envelopes cover more plausible targets at cost of width | Phase 19 large omission, reachable-only 0/512 versus equal envelope 512/512 coverage, zero precise intervals |
| Incorrect cap | A too-small cap can exclude truth | Phase 19 bad mass cap equal envelope 0/512 coverage |
| Hidden-tail violation | An invalid hidden-support restriction can exclude truth | Phase 19 bad hidden support equal envelope 0/512 coverage |
| Missing stratum and nonresponse | Unobserved strata should not be treated as observed zero outcomes | Phase 18 missing stratum combined abstained 512/512. This case combines missingness and nonresponse, so their effects are inseparable |
| Duplicates | Independent-unit counts matter more than billed rows | Phase 19 duplicate block case with block-aware allocation gave 512/512 equal-envelope coverage. The raw checker verifies effective counts and cost separately |
| Wrong weights | Correct-looking metadata and small sampling errors do not repair incorrect mixture weights | Phase 15 wrong-weight case reported 485/512 false certificates in the verified archived replay |
| Threshold boundary | A point exactly .60 is nonpositive. A lower endpoint exactly .60 and high > .60 abstains | Unit tests cover both, and Phase 18 combined abstained 512/512 in near-threshold case |
| Degenerate distributions | A zero-width interval can be valid. Wilson uncertainty remains nonzero at all-zero/all-one outcomes | Unit tests verify point intervals and endpoint Wilson bounds |
| Numerical and integrity failures | Invalid intervals, malformed rows and duplicate keys must fail. Small floating-point differences need an explicit tolerance | NaN, infinity, reversed, out-of-support, missing and duplicate rows fail. Absolute 1e−9 comparisons distinguish floating discrepancies from exact count mismatches |

The reproduction report locks representative counts after archived raw checks. The fixtures do not establish behavior under arbitrary misspecification, differential nonresponse or deployment populations.
