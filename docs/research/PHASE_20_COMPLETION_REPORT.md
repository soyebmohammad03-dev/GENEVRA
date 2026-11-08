# Phase 20 completion report

Phase 20 integrates the measurement studies into a reproducible research repository. It changes the delivery and review workflow and adds a notebook sensitivity analysis. It acquires no new simulator or biological observations.

## What was integrated

The repository guide, inventory, experiment index, methodology matrix, citation record and manuscript foundation make the simulator and measurement program navigable together. The archived Phase 11–19 replay uses each study's original code snapshot, frozen configurations, seed streams and raw sufficient counts. The combined technical archive packages 1,512 copied files plus provenance and checksums, omitting private workspace logs, duplicate nested archives and older renderings. The original archives and evidence remain unchanged. Large generated data are distributed as an asset outside Git history.

A single replay command checks the outer archive and each member, dispatches ten entries, and calls the phase-local independent reconstructions. The notebook compares interval widths within studies, reports certificate risk and coverage separately, and derives the width floor when no reachable samples can inform the inaccessible population. It reuses the frozen benchmark tables rather than rerunning acquisition.

## Evidence and limits

The verified results show an identifiable precision gain when credible tail information is added, and a distinct loss of identification under shared frame blindness. Phase 18 reproduced 0/512 coverage and 180 false certificates under shared blindness. Phase 19's valid coverage envelope restored coverage in its large-omission condition, with no precise intervals. The allocation proxy lost 440 covered precise intervals out of 512 in the primary comparison. These results are synthetic and assumption-conditional. Established partial identification, concentration and allocation explain the mechanisms. The distinct contribution is the frozen, auditable stress workflow and its negative results.

No independent empirical evidence, external review, valid biological reference labels, actual acquisition costs or representative external target population were established. The manuscript foundation is for internal and artifact review. Before reconsidering submission, obtain an independent artifact assessment and one independently specified comparison with documented target inclusion and nonresponse, credible external omission limits, measured acquisition costs and appropriately held-out outcomes.

## Verification and reproducibility

| Check | Result |
|---|---|
| Full local research checkout | 997 passed in 154.82 s, zero failures or skips |
| Clean export of the public tree plus Phase 20 test and replay source | 732 passed in 85.02 s, zero failures or skips |
| Lint, formatting, strict typing and committed evidence | Passed |
| Fresh replay environment | CPython 3.12.15 and NumPy 2.5.4, macOS arm64 |
| All ten replay entries | Passed, 80.91 s wall and 394.2 MiB peak RSS |
| Notebook | Four code cells executed in a fresh kernel after disambiguating the Phase 11 truth level |
| Historical integrity | 10,969 inventoried files byte-identical, 20 original ZIPs CRC-clean |
| Intended historical documentation edits | Top-level README and notebook index only |

The exact commands and fixed dependencies are in the [research guide](README.md). The [archive catalog](archive.json) pins the remote asset and original provenance. The [replay receipt](replay-receipt.json) records phase runtimes. The figure is generated from the [notebook](../../notebooks/certification_evidence.ipynb). The aggregate archive is separate from earlier bundles and does not change their bytes. Independent reconstruction is numerical verification performed inside the project, separate from external peer review.

## File and delivery scope

Updated the root README and notebook index. Added citation metadata, the research guide directory, one notebook, the replay command and five archive integrity test cases. No simulator modules or earlier analysis implementations changed. The GitHub technical prerelease hosts the replay asset, and the research branch contains the integration. The default branch remains main.
