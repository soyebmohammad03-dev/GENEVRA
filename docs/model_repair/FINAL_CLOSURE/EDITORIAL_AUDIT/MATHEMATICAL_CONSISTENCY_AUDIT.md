# Mathematical and statistical consistency

Verification compared the editorial LaTeX and PDF with the [frozen receipt](../../../research/phase_29/rendered/audit-receipt.json), [claim audit](../SCIENTIFIC_CLAIM_AUDIT_FINAL.md), and [Phase 25 contrasts](../../../research/phase_25/contrasts.csv).

| Check | Verified disposition |
|---|---|
| Target and interval definitions | The target mixture and affine score transformation are preserved. Coverage uses inclusive endpoints. Useful precision requires coverage and width at most the declared limit. Threshold labeling and anchor certification remain separate rules. |
| Shared blindness | The combined policy had 0/512 target coverage and 180/512 false certificates per run. Among the 180 issued certificates, 180 were false. There were zero wrong threshold labels. The manuscript distinguishes these endpoints. |
| Simultaneous safety bound | The one-sided upper bound is 40.73% on the per-run false-certification rate. Evaluating the binomial lower tail for 180/512 at the unrounded upper bound gives 0.05/9, for the declared nine-case family. The issued-only fraction is a descriptive count. |
| Matched allocation | At 32,768 charged units the three methods had 1/256, 104/256 and 229/256 covered-and-precise intervals. Each covered 256/256. The registered contrast compares width proxy with paid-pilot Neyman. Equal spend remains descriptive. |
| Paired interval | The difference is (1−104)/256, or −40.234375 percentage points. Applying the declared Hoeffding radius with 256 independent pairs and alpha 0.05 reproduces the reported interval [−57.21, −23.26] percentage points. The 103 discordances favor Neyman. |
| Mean width versus per-run precision | Table 3 preserves means 0.6726, 0.6113 and 0.5576 score units. A mean describes interval width across runs. Useful precision counts require separate per-replicate checks. |
| Inferential limits | The designs use synthetic populations and supplied restrictions. Secondary intervals containing zero do not establish equivalence. Separate numerical implementation and internal replay supply internal verification. Independent validation remains open. |

The editorial build uses the same 12 references, figure assets and result values. The publication-only reconstruction matched the original frozen technical manuscript and receipt. The benchmark campaign was outside this audit.
