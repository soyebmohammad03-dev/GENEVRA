# When sampling frames share a blind spot: a reproducible benchmark for population-mean certification

Soyeb Mohammad | GENEVRA | Research manuscript for independent review

## Abstract

Agreement between sampling channels can leave both channels blind to the same target units. We present GENEVRA, a reproducible benchmark that separates target-mean coverage, interval precision, threshold decisions, and anchor certification under controlled information and costs. In a frozen shared-blindness case, {{shared_cover}} of {{shared_n}} intervals covered the target and all {{shared_false}} issued certificates were false, although no threshold label was wrong. In a separate matched-cost comparison at {{budget}} charged units, GENEVRA's width-proxy allocation gave {{proxy}} of {{n}} covered-and-precise intervals, versus {{neyman}} for paid-pilot cost-adjusted Neyman and {{equal}} for equal spend. The paired proxy-minus-Neyman difference was {{difference}} percentage points (95% Hoeffding interval {{low}} to {{high}}). In a separate large-omission case, applying a valid supplied cap to the same equal-spend acquisitions changed coverage from zero to all runs, with no covered-and-precise intervals. An independent implementation of the numerical calculations, executed internally, recovered the central results. The contribution is an auditable benchmark of these failure modes. Its evidence concerns synthetic populations under stated laws, restrictions and costs.

Keywords: undercoverage, partial identification, stratified allocation, statistical certification, reproducible benchmarking

## 1. Introduction

Sampling precision and target identification answer different questions. A large calibration sample can estimate the distribution on a frame accurately while leaving the population outside that frame unobserved. Two separately sampled channels may agree because they share omissions. An audit that compares only those channels can then admit a policy that reports a precise but wrong target interval or certifies an anchor whose error exceeds the intended tolerance.

The resulting failures can look similar in aggregate. A threshold decision can remain correct when the interval misses the target on the same side of the threshold. A policy can achieve coverage by returning a broad interval, or reduce false certificates by withholding them. A cost-aware allocator can correctly optimize a surrogate loss and still produce fewer useful intervals. The benchmark keeps these outcomes separate so that method comparisons can distinguish sources of failure.

### Research questions and contribution

We ask when shared omission produces false certificates despite agreement, when defensible external restrictions recover target coverage, and how allocation changes useful precision at matched charged cost. A fourth question concerns auditability. Can separate code recover the decisions and comparisons from underlying records? The contribution is the linked suite of frozen stress cases, access and tariff controls, raw-count verification and negative comparisons. Missing-data bounds, confidence intervals and stratified allocation supply the established statistical methods.

## 2. Related work and positioning

Manski [1] and Imbens and Manski [2] distinguish uncertainty about an identified set from sampling uncertainty about the parameter and its bounds. Tudball and colleagues [3] show how auxiliary constraints can inform inference under selection bias. Their application estimates constraints in a different model. GENEVRA supplies restrictions as controlled inputs, including restrictions that are deliberately wrong, and measures their effect on decisions.

Multiple-frame survey methods use probability designs and overlap information to extend access [4]. A spatial probability survey of Norwegian recreational fisheries exposed coverage gaps in alternative frames [5]. This is a field precedent for independently checking coverage. GENEVRA contributes synthetic known truth and matched costs rather than new field evidence. Independent draws from incomplete frames do not supply information about units excluded from both.

Selective classification and held-out calibration distinguish the decisions issued from their errors [6,7]. Our object is a population mean relative to an anchor, with correctness evaluated against declared synthetic truth. Neyman allocation and exact cost-constrained allocation provide variance objectives [8,9]. The width proxy tested here has a different objective. Following the simulation-design distinctions in Morris and colleagues [10], we fix the generating laws, estimands, methods and measures, then separate prespecified contrasts from later sensitivity analyses. The closest prior work limits the originality claim to the specific experimental and verification artifact.

## 3. Mathematical formulation

@table notation Table 1. Core notation. Phase 18 and Phase 25 share the score cutoffs but use distinct certificate constructions.

### Population, frames and information

Let T denote the target and F_A and F_B the subsets reachable by two sampling channels. Shared undercoverage is T outside F_A union F_B. Asymmetric undercoverage excludes a domain in one channel that the other can reach. Independent random draws conditional on each frame say nothing about whether the exclusions overlap. In the frozen shared-blind case the channels observe the source law despite a changed evaluation law. This is a planted common blind spot. The scenario does not estimate the prevalence of correlated omissions.

The reduced allocation model has two reachable strata with known conditional weights w_h summing to one. Outcomes within a stratum are independent Bernoulli tail indicators with rates p_h. Set r = Σ_h w_h p_h and q_T = (1−m)r + mz. The target mean is θ = 0.30 + 234.2 q_T. The conditional body and tail score means are supplied constants. Neither method samples the missing population. The evaluator knows q_T and latent rates for scoring, and operational policies receive the same declared inputs. Only the labeled oracle allocates using true stratum variances.

### Intervals and identification

After an independent pilot, stratum h has k_h successes in n_h independent inference draws. Its point rate is k_h/n_h. For the fixed-look likelihood bounds, retain rates p with log likelihood minus its maximized value at least log(α/4). The factor four accounts for two tails and two strata. Weight the lower and upper endpoints separately to obtain the reachable band [l,u]. A zero observed count gives an analytic upper endpoint, and an all-success count gives the corresponding lower endpoint. The nominal interpretation requires the stated sampling law, weights, and independence of pilot and inference.

Given supplied bounds 0 ≤ m ≤ U and 0 ≤ z ≤ V, the target rate hull is [(1−U)l, u + U max(V−u,0)]. This follows by taking endpoints of the affine expression in m and z for each reachable endpoint. Apply the affine score transformation to the hull. With an exactly known r and V=1 the width is 234.2 U. Reachable sampling cannot remove that identification component. Unknown or invalid restrictions prevent the same interpretation for the full target.

### Coverage, precision and certificates

A score interval [L,H] covers when L ≤ θ ≤ H. Precision means H−L ≤ τ. Useful precision is their intersection. A beneficial label requires L > ε. A nonbeneficial label requires H ≤ ε. Otherwise the policy abstains from threshold classification. The frozen ε and τ are both 0.60, in different roles. The anchor tolerance δ is 0.30 score units.

In Phase 25 a certificate is issued when the entire interval lies inside [a−δ,a+δ]. It is false if issued and |θ−a| > δ. Phase 18 instead constructs a separate bound on source-anchor error from nuisance bands. With estimated source tail rate p_S, target tail band [p_L,p_U] and residual upper bound q_U, its rule requires 239.45 max(|p_L−p_S|,|p_U−p_S|) + 239.55 q_U ≤ δ and policy admission. The target score interval uses the conditional mean bands and the residual term separately. Returning full physical support on rejection does not issue a certificate. Certificate issuance, false certificates per run, false certificates among issued, and threshold abstention have distinct denominators.

@figure diagnostic Figure 1. Diagnostic framework. Top row follows the population interval and threshold call. Bottom row follows the anchor decision and two risk denominators. Boxes are conceptual, with no plotted observations.

## 4. Experimental design and comparators

@figure design Figure 2. Design and reproduction architecture. The upper row shows synthetic information and acquisition. The lower row shows the artifact and numerical verification path. This schematic has no measured quantities.

Phase 18 supplies one common package of a fixed-allocation frame stream, a probability-mixture audit stream, source anchor data and conditional evaluation counts. Direct calibration uses the audit stream. Stratified direct uses the frame. The combined rule uses the stratified band subject to registry checks and a disagreement test. Pooling is available only when declared design and common current-law assumptions justify it. A refusal control returns full support. In shared blindness the independent frame and audit streams sample the same stale law. The evaluation law differs. Conditional body and tail means are estimated using Hoeffding bounds and nuisance masses use Clopper–Pearson bands in this design. The Phase 19 extension isolates known conditional score means and exogenous omission restrictions.

Phase 25 uses nine frozen case laws and two budgets. Each paid policy receives the same pilot of 128 independent draws per stratum. It discards these draws from inference and acquires additional observations from independent streams. Within each replicate, policies use common prefixes of those inference streams to retain paired comparisons. A replicate, rather than a stratum, draw or duplicated row, is the unit of analysis. Duplicated blocks are billed by row and analyzed by independent unit. Pilot and inference together exhaust the synthetic tariff B. Frame enumeration, cap construction, and externally supplied score means are outside this tariff. Operational field costs remain unknown.

The width proxy minimizes Σ_h w_h / sqrt(n_h). Paid-pilot cost-adjusted Neyman minimizes Σ_h w_h² v_h / n_h using smoothed pilot variance v_h. Minimax uses the Bernoulli variance bound one-quarter. Proportional allocation approaches w_h shares in independent units, while equal spend divides charges evenly between strata. All use the same envelope. Direct reachable calibration buys equal-spend inference and omits expansion. It is a diagnostic under incomplete coverage. The true-rate variance oracle has privileged information. A zero-acquisition abstention control is reported separately. None of the latter controls defines a matched-information superiority claim.

## 5. Statistical analysis

Phase 18 scores utility as +1 for a correct certificate, −1 for a false one and 0 for none. Three paired combined-minus-comparator contrasts use an equally weighted mixture of four restricted cases. Replicate differences lie in [−2,2]. Two-sided Hoeffding intervals [11] use α=.05/3. The safety bound in the shared-blind case is the one-sided Clopper–Pearson [12] upper bound for the unconditional false-certification proportion with error .05/9. It belongs to the nine-case combined-policy family. It is distinct from the conditional proportion among issued certificates. This descriptive mixture supplies no deployment weights.

The Phase 25 primary comparison uses small omission at {{budget}} charged units. For independent paired replicates j let D_j be proxy useful-precision indicator minus Neyman useful-precision indicator. Its mean is the estimated difference. Since D_j lies in [−1,1], the radius is sqrt(2 log(2/α)/n) with α=.05, truncated at the possible difference range. The separate secondary family uses α=.05/17 per contrast. The primary improvement rule required the lower endpoint to exceed 0.05. Equal spend comparisons are descriptive here. Zero in an interval does not establish equivalence. The exploratory sensitivity sweep uses a separate seed and one-factor interventions, with no confirmatory ranking.

## 6. Results

### Shared blindness separates coverage and decision safety

The combined policy covered {{shared_cover}}/{{shared_n}} target means and issued {{shared_issued}} certificates. All {{shared_false}} were false. The simultaneous upper unconditional false-certification bound was {{shared_upper}}%. Wrong threshold labels numbered {{shared_wrong_label}} because the missed intervals could remain on the correct side of the threshold. The shared frame agreement was insufficient for the anchor claim.

@figure shared Figure 3. Phase 18 shared blindness. Percentages use the denominator named above each panel. The full-run false-certificate count and among-issued count share a numerator. They answer different risk questions.

@table shared Table 2. Frozen Phase 18 shared-blindness decisions. The one-sided simultaneous risk bound applies to the all-run false-certificate row.

At equal spend in the separate Phase 19 large-omission case, the supplied cap raised coverage from {{large_direct_cover}}/{{large_n}} to {{large_cover}}/{{large_n}} on the same counts. Useful precision was {{large_useful}}/{{large_n}}. The {{large_floor}}-unit identification floor exceeded the precision limit.

### The original allocator lost the primary comparison

At {{budget}} charged units the width proxy gave {{proxy}}/{{n}} covered-and-precise intervals, pilot Neyman {{neyman}}/{{n}} and equal spend {{equal}}/{{n}}. The primary difference was {{difference}} percentage points with 95% interval [{{low}}, {{high}}]. All {{discordant}} discordant pairs favored Neyman. All {{secondary}} adjusted secondary intervals included zero. All three covered every target. The per-replicate width cutoff therefore explains the useful-precision gap. The improvement gate failed.

@table allocation Table 3. Phase 25 primary case. Coverage and useful precision are counts per replicate. Mean width is a summary of complete score intervals, not a classification rule.

@figure allocation Figure 4. Phase 25 primary comparison. Left shows total coverage and covered-and-precise percentages, with useful counts labeled. Right decomposes mean width in score units into weighted stratum bands and omission expansion. The dotted line is the per-replicate width limit, shown for scale.

## 7. Failure analysis and sensitivity

In the primary case the proxy allocated fewer independent units to the high-rate stratum. Its weighted contribution to the mean width was {{proxy_high_stratum_width}} score units, versus {{neyman_high_stratum_width}} for Neyman and {{equal_high_stratum_width}} for equal spend. The corresponding envelope increments were {{proxy_envelope_increment}}, {{neyman_envelope_increment}} and {{equal_envelope_increment}}. For each replicate, the reachable width is 234.2 Σ_h w_h (u_h−l_h). The envelope increment is the final score interval width minus that reachable width. Averaging is linear for this decomposition, but the event “covered and precise” is an indicator of two inequalities on a single replicate. Mean components explain the observed width gap and cannot reconstruct useful counts by comparing a mean with τ. The frozen audit checked integer allocation against the continuous optimum and did not find rounding that could explain the allocation gap.

Neyman's pilot responds to observed variance and shifted draws toward the stratum driving width. Equal spend placed more draws there again under the frozen prices, and led descriptively. Estimating variance from a short pilot can be unstable when hits are rare. Smoothing prevents zero variance estimates and can inflate very small rates. Even true variance optimization does not optimize the tail-sensitive likelihood width or useful precision. The comparison therefore establishes a local objective mismatch under these costs and laws.

@figure sensitivity Figure 5. Selected Phase 26 exploratory interventions. Cells show covered-and-precise counts over the number of synthetic runs. Selection spans pilot, price, omitted mass, cutoff and budget changes. These are descriptive.

@table sensitivity Table 4. Machine-readable extract of the same exploratory cells. The full frozen sensitivity grid also includes invalid weights, bound errors and prevalence changes.

Pilot size changes both variance information and remaining acquisition budget. Large omission and strict width limits produced floor effects, while higher budgets or a loose width limit produced ceilings. Invalid weights and omitted-mass caps could destroy coverage across methods. An invalid hidden-tail restriction could escape detection at small omission because sampling bands remained wide. The separate large-omission invalid-support case retained its negative result. These observations do not provide a policy for diagnosing unknown field assumptions from agreement alone.

## 8. Reproducibility, validity and implications

The public artifact pins source, configuration and archive members. The separate Phase 27 implementation checks {{records}} Phase 25 method-replicate records in {{cells}} cells from counts, reconstructs endpoints and paired intervals, and checks Phase 18 decisions from verified arrays and raw source counts. The historical replay independently reconstructs the Phase 18 arrays upstream. The reference implementation shares the declared design, data and numerical environment. The project executed the reproduction internally. The publication builder derives figures, tables and interpolated result text from frozen machine-readable evidence. The final audit also checks per-replicate width classification and mean-width components from the Phase 25 records. Source and output hashes identify the rendered PDF.

Construct validity depends on the chosen loss. Mean coverage, a correct threshold decision, interval width, and certification each describe a different property. External validity depends on knowing which frames miss which units and whether the omitted component and costs resemble these cases. There is no estimate of synthetic-case prevalence in a field population. The design holds weights and score support fixed in the primary comparison, assumes independence at the replicate level, and uses externally supplied bounds rather than measured field bounds. Wider confidence intervals, conservative refusal, and narrower credible identification sets carry different operational consequences. The benchmark can help distinguish these choices. It supplies no empirical safety estimate or biological validation.

## 9. Conclusion

Shared sampling-frame omissions can defeat certification despite agreement. Valid external information can restore coverage without meeting a precision objective. In the matched small-omission comparison, GENEVRA's width proxy underperformed both the variance-aware and equal-spend allocations on the useful-precision endpoint. That negative result is a test of the benchmark's ability to expose failures under equal information and charges. The next evidence is independent artifact review, a withheld comparison with locked policies for transfer claims, and independently governed frame and outcome measurements for any empirical claim. Journal submission remains on hold.
