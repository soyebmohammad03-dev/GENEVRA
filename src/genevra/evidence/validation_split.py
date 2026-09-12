"""Phase 19.4: development vs. validation seed sets.

A real, non-overlapping split of a seed pool — not a comment claiming
independence. `development_seeds` are the seeds any analysis-design
choice (which metric, which lag, which threshold) was made against;
`validation_seeds` are only ever *evaluated* against a plan already
frozen from the development seeds, never used to change that plan.
"""

from __future__ import annotations

import dataclasses
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class SeedSplit:
    development_seeds: tuple[int, ...]
    validation_seeds: tuple[int, ...]

    def __post_init__(self) -> None:
        if set(self.development_seeds) & set(self.validation_seeds):
            raise ValueError("development_seeds and validation_seeds must not overlap")
        if not self.development_seeds or not self.validation_seeds:
            raise ValueError("both development_seeds and validation_seeds must be non-empty")

    def to_dict(self) -> dict[str, Any]:
        return dataclasses.asdict(self)


def split_seeds(seeds: list[int], n_validation: int) -> SeedSplit:
    """The last `n_validation` seeds (by value, deterministic — not a
    random shuffle, so the split itself is reproducible from `seeds`
    alone) become the validation set; everything else is development."""
    if n_validation < 1 or n_validation >= len(seeds):
        raise ValueError("n_validation must be between 1 and len(seeds) - 1")
    ordered = sorted(seeds)
    return SeedSplit(
        development_seeds=tuple(ordered[:-n_validation]),
        validation_seeds=tuple(ordered[-n_validation:]),
    )


__all__ = ["SeedSplit", "split_seeds"]
