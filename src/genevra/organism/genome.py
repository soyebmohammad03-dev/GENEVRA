"""The genome: inherited information, structured but extensible.

Genes are grouped by concern (controller weights, metabolic parameters,
mutation parameters, learning parameters) rather than one flat vector, so
new gene groups (memory parameters, morphology, ...) can be added later as
new fields without reinterpreting existing ones. `Genome` is the genotype;
`genevra.organism.phenotype.develop` maps it to a `Phenotype` — the two are
never the same object.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from genevra.arrays import FloatArray


@dataclass(frozen=True)
class ControllerArchitecture:
    """Fixed shape of the neural controller a genome encodes.

    Architecture is not itself evolved yet (see docs/organism.md) — it is
    shared configuration that determines how many parameters
    `controller_weights` must contain and how they are reshaped into
    weight matrices.
    """

    input_size: int
    hidden_size: int
    output_size: int

    def __post_init__(self) -> None:
        if min(self.input_size, self.hidden_size, self.output_size) <= 0:
            raise ValueError("architecture sizes must be positive")

    @property
    def num_params(self) -> int:
        hidden_params = self.input_size * self.hidden_size + self.hidden_size
        output_params = self.hidden_size * self.output_size + self.output_size
        return hidden_params + output_params


@dataclass(frozen=True, eq=False)
class Genome:
    """An organism's heritable information.

    `eq=False`: dataclass-generated equality on NumPy array fields raises
    on the ambiguous-truth-value comparison, so identity/explicit
    array comparisons are used instead where genomes need comparing.
    """

    architecture: ControllerArchitecture
    controller_weights: FloatArray
    metabolic_genes: FloatArray
    mutation_genes: FloatArray
    learning_genes: FloatArray

    def __post_init__(self) -> None:
        _require_shape(
            self.controller_weights, (self.architecture.num_params,), "controller_weights"
        )
        _require_shape(self.metabolic_genes, (4,), "metabolic_genes")
        _require_shape(self.mutation_genes, (2,), "mutation_genes")
        _require_shape(self.learning_genes, (1,), "learning_genes")

    @classmethod
    def random(cls, architecture: ControllerArchitecture, rng: np.random.Generator) -> Genome:
        """A fresh random genome, for seeding an initial population."""
        return cls(
            architecture=architecture,
            controller_weights=rng.normal(0.0, 0.5, architecture.num_params).astype(np.float32),
            metabolic_genes=np.array([0.5, 0.1, 0.2, 0.05], dtype=np.float32),
            mutation_genes=np.array([0.1, 0.1], dtype=np.float32),
            learning_genes=np.array([0.05], dtype=np.float32),
        )


def _require_shape(array: FloatArray, shape: tuple[int, ...], name: str) -> None:
    if array.shape != shape:
        raise ValueError(f"{name} must have shape {shape}, got {array.shape}")
