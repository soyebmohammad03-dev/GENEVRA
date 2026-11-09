# Internal adversarial manuscript audit

These are three project-generated review perspectives. No external reviewer participated.

## Reviewer 1. Statistical methodology

- **Major.** The safety percentage can be confused with conditional risk. The paper now identifies the 40.73% bound as one-sided, simultaneous across nine cases, and unconditional over 512 runs. The 180/180 conditional result has its own denominator.
- **Major.** Phase 18 and Phase 25 originally risked reading as one certificate rule. The methods now state the Phase 18 nuisance bound and the Phase 25 interval containment criterion separately.
- **Major.** Mean weighted width components cannot determine a nonlinear per-replicate threshold. The revision defines the exact decomposition and classifies coverage and precision before averaging. Figure 4 identifies the cutoff as per-replicate.
- **Minor.** Missing binomial-limit reference and distinction between Hoeffding families. Added Clopper–Pearson and Hoeffding references, explicit range and error splits, and a notation table.
- **Open.** Conditional risk after issuance in a representative population and uncertainty in estimated omission bounds remain unidentified.

## Reviewer 2. Novelty and significance

- **Major.** Identification under missingness and cost-adjusted allocation are established. Related work now distinguishes Manski, Imbens–Manski, Tudball and colleagues, and Neyman/Wright from the frozen experimental and software choices.
- **Major.** No evidence that a standalone benchmark is distinctive enough for a software journal. The contribution statement is limited to the specific shared-omission cases, access and tariff controls, and public reference pathway. The nearest field analogue and closest software are named.
- **Minor.** Title and abstract could imply a successful allocation strategy. Both now make the loss and auditability central.
- **Open.** Independent use and direct comparison to the nearest available artifact are necessary before claiming added practical value. No priority claim survives on the current evidence.

## Reviewer 3. Design, reproducibility and validity

- **Major.** Real cost is not established by matched row tariffs. The paper now describes charged pilots, inference, duplication, oracle privilege, refusal and omitted field acquisition costs.
- **Major.** Separate code may be mistaken for independent researcher validation. The text describes project execution, raw-count inputs and the Phase 18 shared endpoint arrays. External review remains outstanding.
- **Minor.** Exploratory figures and failure cases require visible provenance. Added counts, denominators, explicit exploratory captions, build receipt and CSVs.
- **Open.** An external frame audit, held-out comparison, nonresponse dispositions and measured costs are absent. An approved prospective protocol and independently governed references would be required for field interpretation.

The draft may be circulated for technical review. Submission remains on hold. No unresolved objection was treated as resolved by wording alone.
