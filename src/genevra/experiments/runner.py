from __future__ import annotations

from genevra.evolution.engine import EvolutionEngine
from genevra.experiments.config import ExperimentConfig
from genevra.experiments.result import ExperimentResult, current_software_metadata


class ExperimentRunner:
    def __init__(self, config: ExperimentConfig) -> None:
        self._config = config
        self.engine: EvolutionEngine | None = None

    def run(self) -> ExperimentResult:
        self.engine = EvolutionEngine(self._config.evolution)
        self.engine.run()
        return ExperimentResult(
            name=self._config.name,
            seed=self._config.evolution.seed,
            status=self.engine.status.value,
            software=current_software_metadata(),
            trajectory=self.engine.trajectory.to_dict(),
            lineage=self.engine.lineage.to_dicts(),
            final_population_size=self.engine.population.size,
            generations_completed=self.engine.generation,
        )
