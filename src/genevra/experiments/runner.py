from __future__ import annotations

import dataclasses

from genevra.evolution.engine import EvolutionEngine
from genevra.experiments.config import ExperimentConfig
from genevra.experiments.result import ExperimentResult, current_software_metadata


class ExperimentRunner:
    def __init__(self, config: ExperimentConfig, condition_id: str | None = None) -> None:
        self._config = config
        self._condition_id = condition_id
        self.engine: EvolutionEngine | None = None

    def run(self) -> ExperimentResult:
        """Runs the experiment. Any exception raised anywhere in the run
        is caught and turned into a `status="failed"` result with a
        populated `failure` field, rather than propagating — a failed run
        must be representable and inspectable, never silently lost or
        allowed to crash a larger comparison it is part of."""
        status = "failed"
        failure: dict[str, str] | None = None
        trajectory: list[dict[str, object]] = []
        lineage: list[dict[str, object]] = []
        final_population_size = 0
        generations_completed = 0
        try:
            self.engine = EvolutionEngine(self._config.evolution)
            self.engine.run()
            status = self.engine.status.value
            trajectory = self.engine.trajectory.to_dict()
            lineage = self.engine.lineage.to_dicts()
            final_population_size = self.engine.population.size
            generations_completed = self.engine.generation
        except Exception as exc:  # noqa: BLE001 - deliberately broad, see docstring
            failure = {"type": type(exc).__name__, "message": str(exc)}

        return ExperimentResult(
            name=self._config.name,
            seed=self._config.evolution.seed,
            status=status,
            software=current_software_metadata(),
            trajectory=trajectory,
            lineage=lineage,
            final_population_size=final_population_size,
            generations_completed=generations_completed,
            environment_summary=dataclasses.asdict(self._config.evolution.environment_config),
            condition_id=self._condition_id,
            failure=failure,
        )
