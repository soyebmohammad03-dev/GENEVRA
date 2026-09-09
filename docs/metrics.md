# Metrics: Fitness, Diversity, Novelty, Evolvability

Module: `genevra.metrics` (`fitness_metrics.py`, `behavior.py`,
`diversity.py`, `novelty.py`, `evolvability.py`, `trajectory.py`).

These are measurements, not conclusions. No metric here proves a
population is "open-ended," has "emergent intelligence," or has "evolved
evolvability." They are instruments for investigating GENEVRA's research
questions, not answers to them — see `genevra/metrics/__init__.py` for the
same statement in the code itself.

## Fitness vs. diversity vs. novelty vs. evolvability

These four are easy to conflate and are kept structurally separate:

- **Fitness** (`genevra.evolution.fitness`, summarized here by
  `fitness_metrics.compute_fitness_summary`) is a scalar derived from one
  individual's raw lifetime observations by a configurable
  `FitnessFunction`. It answers "how well did this individual do,
  according to the criterion this experiment chose."
- **Genotypic diversity** (`diversity.genotypic_diversity`) is mean
  pairwise distance between genome parameter vectors
  (`controller_weights`). It answers "how different are these genomes,"
  nothing about behavior.
- **Behavioral diversity** (`diversity.behavioral_diversity`) is mean
  pairwise distance between behavioral signatures
  (`behavior.behavioral_signature`) — derived from what organisms actually
  did (survival duration, resources gained, spatial displacement/coverage,
  action-use distribution), not from their genomes. Two genomes can be
  nearly identical yet behave very differently under a plastic controller,
  or vice versa; conflating genotypic and behavioral diversity would
  silently discard that distinction. `tests/test_diversity.py::test_behavioral_diversity_is_a_separate_computation_from_genotypic`
  constructs exactly this case (identical genomes, different behavior) to
  keep the two from drifting back together.
- **Novelty** (`novelty.NoveltyArchive.score`) is distance from a
  reference archive of past behavioral signatures. It is not fitness under
  another name: an organism can have high fitness and low novelty (doing
  the same successful thing as everyone else) or low fitness and high
  novelty (doing something unusual and unrewarded).
  `tests/test_novelty.py::test_novelty_is_not_fitness_under_another_name`
  constructs two organisms with identical fitness by construction and
  shows their novelty scores differ.
- **Evolvability** (`evolvability.EvolvabilityAnalyzer`) is a mutation-
  neighborhood measurement for one genotype, on demand — not a per-
  generation population statistic, and not a property stored on a genome.
  See below.

## Behavioral signature

`behavior.behavioral_signature(observations)` maps `LifetimeObservations`
(raw, uninterpreted — see `docs/architecture.md`'s note on
`genevra.evolution.lifetime`) to a fixed-length vector: survival duration,
total resources gained, net spatial displacement, unique-cell coverage,
and the distribution over the six actions (10 features total). This is a
discretized summary, not a learned embedding, and applies no feature
standardization — the scalar features and the action-fraction features sit
on different natural scales, so distance metrics computed directly on this
vector are dominated by whichever raw feature has the largest scale. This
is a documented limitation, not a silently accepted one. Swapping in a
richer representation (full trajectory distance, a learned embedding)
requires only replacing this function — every caller depends solely on its
signature: `LifetimeObservations -> FloatArray` of fixed length.

## Distance abstraction

`diversity.DistanceMetric` is a `Protocol` with two implementations,
`EuclideanDistance` and `CosineDistance` (1 − cosine similarity, returning
the maximal distance for a zero vector, where cosine similarity is
undefined). `mean_pairwise_distance` computes the mean over all (or, via
`max_pairs`, a sampled subset of) pairs of vectors, returning `0.0` for
fewer than two vectors — there is no diversity to measure among fewer than
two individuals. `genotypic_diversity` and `behavioral_diversity` are thin
wrappers over the same function, operating on different inputs (genome
vectors vs. behavioral signatures).

## Novelty archive

`NoveltyArchive` holds a size-capped set of behavioral signatures,
evicting randomly once full (`ponytail`-marked in code — a smarter
retention policy, e.g. evict-least-novel, is future work, not a permanent
ceiling). `score(signature, distance, k)` returns the mean distance to the
`k` nearest archive neighbors (classic Lehman & Stanley novelty search),
or `0.0` for an empty archive. `EvolutionEngine` maintains one persistent
archive across a run's generations, scoring each generation's individuals
against the archive *before* adding that generation's signatures to it —
so early generations score against a small archive and later generations
against a fuller one. This is one concrete reference-set choice (a
persistent historical archive); "current population" or "per-lineage"
archives are conceptually equally valid reference sets the same
`NoveltyArchive` interface could support, not implemented here.

## Evolvability: an operational, mutation-neighborhood definition

GENEVRA's long-term research direction includes "can evolvability itself
evolve?" — unanswerable without a measurable, defensible operational
definition, since evolvability is not a property that can simply be read
off a genome.

**The definition used here:** for a given genotype, sample a controlled
number of mutations (`EvolvabilityAnalyzer(..., num_samples=N)`), develop
each mutant's phenotype, run each through a caller-supplied
`behavioral_evaluator` (typically: `develop()` the genome, run one short
lifetime via `genevra.evolution.lifetime.run_single_lifetime`, summarize
with `behavioral_signature`), and report:

- `viable_fraction` — the fraction of sampled mutants whose evaluator
  didn't raise (didn't produce shape errors, invalid architecture, etc.);
  with the current `GaussianMutation` operator, which never breaks
  controller-weight shapes, every sample is viable, so this is currently
  always `1.0` — the hook exists for future mutation operators (e.g. ones
  that can alter architecture) that could produce inviable offspring.
- `mean_behavioral_distance` / `behavioral_distance_std` — how far the
  *viable* mutants' behavior is from the original genotype's, measured
  with a configurable `DistanceMetric`.

**This is a measurement of mutational variation, not of adaptive success.**
A genotype whose mutational neighborhood produces large, diverse
behavioral changes is not automatically "more evolvable" in the sense of
being more likely to adapt usefully: large undirected variation can mean
fragility (most variants behave worse or die) just as easily as latent
adaptive potential. Distinguishing "produces variation" from "produces
*useful* variation" requires selection acting on that variation over
actual generations — which `EvolvabilityAnalyzer` does not perform. Every
`EvolvabilityReport` carries this caveat verbatim in its
`limitation_note` field, so it travels with the result rather than living
only in documentation.

`num_samples` defaults to a small number (16) and is not run per
generation by default — `EvolutionEngine` never calls
`EvolvabilityAnalyzer` on its own; it is invoked on demand (the baseline
experiment's optional `--evolvability-samples` flag is one example) so
that mutation-sweep cost stays a deliberate choice, not an automatic
per-generation tax.

## Population trajectories

`trajectory.GenerationSnapshot` is an explicit, flat schema (generation
index, `FitnessSummary`, genotypic/behavioral diversity, mean novelty,
survival rate, reproductive success rate, mean heritable mutation
rate/sigma, genome/behavior centroid shift from the previous generation,
and an `extinction` flag) rather than an arbitrary object graph.
`Trajectory.to_dict()` produces plain nested dicts/lists/primitives —
directly `json.dumps`-able, and a natural starting point for a future
CSV/Parquet exporter without redesigning storage.

`genome_centroid_shift`/`behavior_centroid_shift` are the Euclidean
distance between this generation's mean genome (resp. behavioral
signature) vector and the previous generation's — a cheap, first
approximation of "how much did the population change this generation,"
`None` for the first recorded generation (no previous centroid to compare
against). `extinction` is set (and the run stops) when no individual met
the reproduction eligibility threshold in that generation — this is
recorded in the trajectory, not silently discarded; see
`docs/architecture.md`'s note on `EvolutionEngine.step()`.
