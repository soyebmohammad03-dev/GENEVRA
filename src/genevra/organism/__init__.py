"""Digital organism foundation: genome, phenotype, controller, sensing,
memory, learning, metabolism, mutation, and reproduction — as separate,
composable components rather than one monolithic `Organism` class.

The central separation this package exists to preserve:

- **Genome** (`genome.py`): inherited, heritable information. Mutated only
  between generations.
- **Phenotype** (`phenotype.py`): a deterministic *development* of a
  genome (`develop()`) — never mutated directly, never stored as the
  source of truth.
- **Lifetime state** (`memory.py`, `learning.py`'s `LearningState`):
  changes within one organism's life and is discarded when it dies. Never
  written back into the genome.
- **Learning control parameters** (`LearningParams`, from
  `genome.learning_genes`): heritable parameters that govern *how*
  lifetime learning happens (e.g. a learning rate), distinct from both the
  inherited weights being learned on top of and the plastic state itself.

This A/B/C split (inherited parameters / lifetime-learned state /
heritable control of learning) is what makes "can learning strategies
themselves evolve?" an answerable question in this codebase rather than a
hardcoded assumption.
"""
