# Matched-budget comparisons

At 32,768 charged units, equal spend acquired (16,384, 8,192) independent outcomes and the proxy-optimal plan acquired (25,378, 3,695). Prices were 1 and 2. Neither design sampled inaccessible outcomes. The abstention baseline costs zero and returns full support. It is a refusal control, not an equal-budget estimator. No direct-access oracle was included as a contestant. The exact reachable-law identification width is a descriptive reference.

| Case at 32,768 | Reachable-only coverage | Equal envelope coverage | Planned envelope coverage | Equal / planned median width |
|---|---:|---:|---:|---:|
| Complete | 512 | 512 | 512 | .439 / .552 |
| Small omission | 512 | 512 | 512 | .554 / .667 |
| Large omission | 0 | 512 | 512 | 1.606 / 1.722 |
| Shifted reachable | 511 | 512 | 512 | .673 / .845 |
| Near threshold | 512 | 512 | 512 | .422 / .467 |
| Verified hidden support | 512 | 512 | 512 | .461 / .573 |
| Bad mass cap | 0 | 0 | 0 | .555 / .669 |
| Bad hidden support | 0 | 0 | 0 | .461 / .573 |
| Duplicates | 512 | 512 | 512 | 1.448 / 1.758 |

Every count is out of 512 synthetic runs. The full JSON reports both budgets, Wilson intervals, all methods and all metrics. For the primary case, 450/512 equal-spend intervals covered and met width .60 versus 10/512 planned. The paired difference was −.859375, 95% Hoeffding interval [−.979415, −.739335]. The prespecified improvement gate failed. This is evidence against the frozen allocation proxy for this rare-event law, without implying equal spend is generally optimal.

The reachable-only large-omission policy issued 350 false certificates. The valid envelopes issued zero, with no narrow intervals. It is a trade of precision for validity. The theoretical irreducible width of 1.171 in that case explains why increasing only reachable sampling cannot restore .60 precision.
