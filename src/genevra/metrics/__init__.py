"""GENEVRA's scientific measurement layer: measuring what happens during
evolution, not just running it.

These are measurements, not conclusions. In particular:

- **Fitness** (`fitness_metrics.py`) summarizes the scalar fitness values
  `genevra.evolution.fitness` already computed — it does not redefine
  fitness.
- **Diversity** (`diversity.py`) is split into *genotypic* diversity
  (distance between genome parameter vectors) and *behavioral* diversity
  (distance between behavioral signatures derived from what organisms
  actually did). These are not the same quantity and are never conflated:
  two genomes can be nearly identical yet behave very differently (or vice
  versa), and only measuring one of them answers only half the question.
- **Novelty** (`novelty.py`) measures distance from a reference archive of
  past behavior. It is not fitness under another name — an organism can
  have high fitness and low novelty (doing the same successful thing
  everyone else does), or low fitness and high novelty (doing something
  unusual and unrewarded).
- **Evolvability** (`evolvability.py`) is an operational, mutation-
  neighborhood measurement — how much phenotypic/behavioral variation a
  genotype's immediate mutational neighborhood produces — not a claim
  about long-run adaptive potential. See that module's docstring for the
  distinction between mutational variation and adaptive success.

No metric here is evidence that a population is "open-ended," has
"emergent intelligence," or has "evolved evolvability" in any strong
sense. They are instruments for investigating those questions, not answers
to them.
"""
