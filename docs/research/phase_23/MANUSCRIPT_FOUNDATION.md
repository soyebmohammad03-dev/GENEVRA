# Manuscript foundation for review

## Title candidates

1. **When Calibration Cannot Resolve Shared Undercoverage: A Reproducible Stress Benchmark**
2. **Precision, Identification and Abstention Under Matched Information Access**
3. **Testing Anchor Certification When Calibration and Evaluation Share Blind Spots**

## Abstract draft

Calibration may reduce uncertainty within observed strata while leaving a target mean unidentified under shared frame omissions. We assemble a reproducible benchmark of this distinction using bounded synthetic paired-score laws, fixed information packages and explicit abstention and certification rules. In a shared-blindness case, 180 of 512 synthetic runs issued false anchor certificates and none achieved mean coverage, even though no threshold directions were wrong. In a subsequent large-omission case, supplying a valid cap on omitted mass restored coverage from zero to all 512 runs while producing no precise intervals. The tested cost planner performed worse than its equal-spend comparator on covered-and-precise output in a separate frozen comparison. A public Census reconstruction illustrates an aggregate coverage discrepancy and supplies no matched policy outcomes. The benchmark contributes replayable failure cases and assumptions that a future independent reference study must test.

## Contribution and gap

Established partial identification, bounded inference, frame sampling and abstention methods already address the component problems. The contribution under review is a frozen stress benchmark connecting shared omissions to three distinct failures under stated access and costs. Those endpoints are target mean coverage, false anchor certification and low useful precision. A claim that this benchmark fills a practical gap still requires comparison to existing benchmark suites and evaluation by independent users.

## Methods outline

- Write the declared synthetic target as \(\mu=(1-p)c+pt+qd\), where \(p\) is tail mass, \(c,t\) are conditional score means and \(q,d\) describe the residual mass and mean. In the fixed-mean extension with no residual, \(p=(1-m)r+mz\) for reachable tail rate \(r\), omitted mass \(m\) and hidden tail rate \(z\). For exact \(r\), \(z\in[0,1]\), and \(m\in[0,U]\), the reachable rate maps to \([(1-U)r,(1-U)r+U]\). The fixed score span \(t-c>0\) maps this to width \((t-c)U\). The result assumes the declared support and a valid \(U\).
- Use each phase's frozen estimators, seeds and sampling laws. In matched policy comparisons keep the same acquired data and costs. Contrast direct calibration, restricted transfer, the combined rule and abstention as applicable. Separate preferential access controls and comparisons across acquisition plans.
- For a target interval \(I\), mean coverage is \(\mu\in I\). A threshold decision resolves the .60 boundary. An anchor certificate requires \(I\subseteq[a-.30,a+.30]\) under the frozen synthetic tolerance. Record precision and abstention separately. Report all-run denominators and risk among issued if that denominator is nonzero. Synthetic runs are replicate units.
- Report each phase's own interval construction and multiplicity, including Phase 18 simultaneous safety and paired utility. Describe the mixture weights and charged costs explicitly. Keep paired rather than unpaired comparisons where common random inputs were used.
- Reconstruct Census percentages with publisher vintages and exact national rows. Label these as descriptive diagnostics. Do not pool them with synthetic replicate outcomes.

## Results outline and discussion

1. Present the [identification floor](../identification_floor.png), including the .60 precision and 234.2 span assumptions.
2. Present shared blindness, failed safety, and uncertain paired utility before the valid-cap recovery. Keep wrong threshold calls separate from false certificates. Report paired utility versus direct +.1064 [−.0303, .2432], stratified +.0962 [−.0406, .2329], and abstention +.0039 [−.1328, .1407] in the frozen comparison.
3. Show the failed matched-budget allocation contrast alongside the coverage recovery. Separate cost proxy optimality from measured precision.
4. Present the [Census diagnostic](../phase_21/census_diagnostic.png) separately, with the limits of net discrepancy.
5. Put the [proposed prospective study](../phase_22/PROTOCOL.md) in future work. Explain what independently governed reference access, actual cost measurement and powered comparisons would change.

## Limitations and claim boundaries

Only the declared synthetic laws are assessed. Known omitted mass and hidden support are idealized unless independently justified. Separate seeds leave common frame errors intact. The charged cost schedule and scenario mixture are design assumptions. Synthetic replications do not imply population-level field evidence. The Census reconstructions use related aggregate estimates without unit-level overlap or matched interventions. Field safety, useful gain, reference reliability and biological validity remain open. No claim of a new estimator, universal superiority, or journal readiness is made.
