# GENEVRA public reproduction challenge

GENEVRA studies bounded-score certification when acquisition and calibration share gaps in their sampling frames. This challenge offers frozen synthetic cases where the true target is known to the evaluator. It includes both successful and failed decisions. The cases establish neither field performance nor biological validity.

Choose a track.

- **Reproduction.** Start from the public research branch, use the pinned environment, replay the capsule, and compare independently reconstructed numbers and regenerated figures. Follow the [commands](REPRODUCE.md).
- **Competing implementation.** Use the exported Phase 18 acquisition package to implement a fixed policy and return per-replicate decisions. The scorer supplies common endpoints and an exploratory paired comparison. Follow the [specification](SPECIFICATION.md).

The [dependency map](DEPENDENCIES.md) explains which inputs underlie each result and which calculations share code. The [adversarial matrix](ADVERSARIAL.md) distinguishes theoretical expectations, observed synthetic results and deterministic scorer tests. The [completion report](PHASE_24_COMPLETION_REPORT.md) records the readiness gates.

The public capsule exposes scenario truth. Results are suitable for audit and transparent exploratory comparisons. A credible confirmatory competition would require a separately governed held-out suite with policy locking and unblinding procedures. No external participant has reproduced or submitted results to this challenge.
