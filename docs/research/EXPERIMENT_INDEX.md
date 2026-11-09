# Frozen experiment index

After replay, each `archive/phase-*` directory contains the copied frozen sources, available inputs, sufficient raw observations and expectations. Each `phase-*` output is newly reconstructed. The archive retains historical counts, thresholds, scenario names and sample-size units.

| Phase | Question and required assumptions | Frozen outcome | Archive entry |
|---|---|---|---|
| 11 | Can fixed-width bounded inference be improved using betting under known law and independence? | Width improved. Near-threshold precision gate failed. | phase-11/reproduce.sh |
| 12 | How much precision is possible with known tail mass and narrow valid support? | Conditional synthetic gate passed. Incorrect mass, hidden support and dependence threaten inference. | phase-12/reproduce.sh |
| 13 | Can independent calibration learn nuisance tail and residual masses? | Conditional feasibility passed with sufficiently large independent calibration. | phase-13/reproduce.sh |
| 14 | Does source calibration transfer after target change? | Transfer gate failed. Representative audits found large changes, while blind audits missed them. | phase-14/reproduce.sh |
| 15 | Can a representative probability frame bound source-anchor error? | Conditional frame gate passed. Wrong weights, blindness and post-audit shifts defeated unrestricted transfer. | phase-15/reproduce.sh |
| 16 | Does an independent rate audit catch invalid frame metadata? | Shared blindness passed the audit, with 0/256 coverage and 95 false certificates. Direct had privileged target access. | phase-16/reproduce.sh |
| 17 | Do equal row counts establish equal access or cost? | Independent comparison audit identified the access asymmetry and no external validating target. | phase-17/reconstruct.py |
| 18 | Is the combined policy superior with the same acquired information? | No superiority. Shared blindness gave 0/512 coverage and 180 false certificates, simultaneous upper 40.73%. | phase-18/reproduce.sh |
| 19 audit | Can a separate implementation recover Phase 18? | 9 cases and 4,608 replicates reconstructed, with no publication qualification. | phase-19/docs/verify_phase18.py |
| 19 extension | What can valid omission bounds recover, and does a width proxy allocate samples well? | Valid envelope recovered large-omission coverage. The planned allocation lost 440 covered precise intervals out of 512 in the primary cell. Invalid assumptions caused failures. | phase-19-extension/experiments/coverage_envelope_study.py |

Phases 1–10 remain in the historical workspace and original evidence corpus. The public replay intentionally covers Phases 11–19 and includes only the earlier dependency slices required by those studies. The original public simulator [experiment catalog](../experiments.md) and [evidence directory](../../research_evidence/README.md) have separate reproduction commands. The two Phase 19 artifacts are distinct.
