"""The genotype-to-phenotype map.

`develop()` is a pure function of a `Genome` — no randomness, no hidden
state — producing a `Phenotype`: the built controller and the structured,
named parameter groups the rest of the organism's components consume.
Keeping this a separate step (rather than organism components reading
`genome.*_genes` arrays directly) is what will let later work study
genotype-to-phenotype maps themselves — e.g. redundant encodings, robustness
to mutation — without changing the genome's shape.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from genevra.organism.controller import Controller
from genevra.organism.genome import Genome
from genevra.organism.learning import LearningParams
from genevra.organism.metabolism import MetabolicParams


@dataclass(eq=False)
class Phenotype:
    controller: Controller
    metabolic_params: MetabolicParams
    learning_params: LearningParams


def develop(genome: Genome) -> Phenotype:
    controller = Controller.from_weights(genome.architecture, genome.controller_weights)
    move_cost, stay_cost, eat_cost, base_upkeep = (float(gene) for gene in genome.metabolic_genes)
    metabolic_params = MetabolicParams(
        move_cost=move_cost, stay_cost=stay_cost, eat_cost=eat_cost, base_upkeep=base_upkeep
    )
    learning_rate, plasticity_gate, decay = (float(gene) for gene in genome.learning_genes)
    learning_params = LearningParams(
        learning_rate=learning_rate,
        plasticity_gate=float(np.clip(plasticity_gate, 0.0, 1.0)),
        decay=float(np.clip(decay, 0.0, 1.0)),
    )
    return Phenotype(
        controller=controller, metabolic_params=metabolic_params, learning_params=learning_params
    )
