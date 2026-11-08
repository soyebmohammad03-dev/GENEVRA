# GENEVRA information and assumption ledger

The target is a bounded score mixture with two reachable Bernoulli strata and a possibly inaccessible population portion. The base score has support [0.3,234.5]. All matched methods observe the same pilot counts and know nominal weights and linear independent-unit tariffs. They purchase their allocated inference draws independently of the pilot. The evaluator alone knows latent mass, tail rates, target mean and correctness. Complete access and independent sampling within each reachable stratum, positive true stratum weights, and valid supplied caps are required for the envelope's nominal coverage interpretation. Duplicate rows are not independent replicates.

| Method and status | Before inference | After acquisition and assumptions |
|---|---|---|
| Width proxy, unsuccessful allocation approach kept as comparator | Weights and prices. Sees but ignores pilot | Common confidence procedure. Optimizes an upper-width proxy instead of realized interval width |
| Paid-pilot Neyman, operational comparator | Weights, prices and smoothed pilot variance estimates | Same envelope. Optimizes estimated variance. Pilot error affects allocation while independent inference protects fixed-look validity under correct assumptions |
| Equal spend, operational comparator | Known linear prices. Pilot is shared and unused | Same envelope and exact budget. No variance estimates required |
| Proportional, operational comparator | Nominal stratum weights and costs. Pilot unused | Same envelope. Integer implementation near proportional units |
| Minimax variance, operational control | Worst-case Bernoulli variance bound of .25 and weights/costs | Same envelope. Minimax is for variance over all Bernoulli rates, with no analogous certificate guarantee |
| Direct reachable calibration, diagnostic | Equal-spend acquisition. Omits mass expansion | Valid as full-target inference under complete access or independently established equality of reachable and target laws. Under omission it is an assumption-violation control |
| True-rate variance oracle, privileged diagnostic | Also sees true stratum probabilities | Same priced observations and envelope. Exact true-variance optimum under the objective. Excluded from equal-information superiority claims |
| Always abstain, conservative control | Buys no observations | Returns full physical range and no certificate. Utility and risk interpreted as a refusal policy at a different cost |

External mass and hidden-tail caps are supplied to every eligible envelope method, outside the tariff. A certificate is issued only if its entire interval lies within the anchor tolerance. Validity of that inference depends on coverage and correct identification restrictions. False certification among issued decisions differs from all-run false certification. Conditional safety requires its own representative reference and protocol. Neither good observed coverage nor an abstention choice identifies missing outcomes. Results at a changed nominal level in the sweep describe that synthetic sampling rule only.

The benchmark excludes unknown numbers of reachable strata, estimated population weights, missing inference samples within a reachable stratum, and nonlinear frame costs. The Phase 18 missing-stratum and shared-frame counterexamples remain archived, with a different protocol. Phase 26's omitted-mass sensitivity changes the inaccessible fraction, not the availability of either reachable stratum.
