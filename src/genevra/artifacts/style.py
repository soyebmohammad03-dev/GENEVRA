"""Phase 14.2: one shared matplotlib style + a save-with-metadata helper,
so every figure in `genevra.artifacts.figures` looks consistent and
carries a machine-readable sidecar (Phase 14.5).

`matplotlib` stays an optional, lazily-imported dependency, exactly like
`genevra.visualization` — this module never imports it at module scope.
"""

from __future__ import annotations

import dataclasses
import json
import subprocess
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from matplotlib.figure import Figure

_MISSING_MATPLOTLIB = (
    'matplotlib is required for genevra.artifacts. Install it with: pip install -e ".[viz]"'
)


def require_matplotlib() -> Any:
    try:
        import matplotlib.pyplot as plt
    except ImportError as exc:  # pragma: no cover - exercised only without the optional dep
        raise ImportError(_MISSING_MATPLOTLIB) from exc
    return plt


def apply_style() -> None:
    """Consistent typography/sizing across every figure this package
    produces. Called once by every `genevra.artifacts.figures` function
    before creating a figure — idempotent, no game-like decoration
    (no gradients, no 3D, a fixed serif-free scientific-plot font)."""
    plt = require_matplotlib()
    plt.rcParams.update(
        {
            "figure.figsize": (6.0, 4.0),
            "figure.dpi": 150,
            "font.size": 10,
            "axes.titlesize": 11,
            "axes.labelsize": 10,
            "legend.fontsize": 9,
            "axes.grid": True,
            "grid.alpha": 0.3,
            "axes.spines.top": False,
            "axes.spines.right": False,
        }
    )


def _git_commit() -> str | None:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"], capture_output=True, text=True, timeout=5, check=False
        )
    except (OSError, subprocess.SubprocessError):  # pragma: no cover - environment-dependent
        return None
    if result.returncode != 0:
        return None
    return result.stdout.strip()


@dataclass(frozen=True)
class FigureMetadata:
    figure_id: str
    experiment_id: str
    data_source: str
    metrics: tuple[str, ...]
    analysis_version: str
    seed_policy: str
    creation_timestamp: str
    git_commit: str | None
    parameters: dict[str, Any]
    caption: str
    limitations: str
    files: tuple[str, ...] = field(default_factory=tuple)
    """Relative filenames actually written for this figure (e.g. one PNG,
    optionally an SVG) — the sidecar names exactly what exists on disk."""

    def to_dict(self) -> dict[str, Any]:
        return dataclasses.asdict(self)


def save_figure(
    fig: Figure,
    output_dir: Path,
    figure_id: str,
    experiment_id: str,
    data_source: str,
    metrics: tuple[str, ...],
    caption: str,
    limitations: str,
    analysis_version: str = "artifacts.figures.v1",
    seed_policy: str = "n/a",
    parameters: dict[str, Any] | None = None,
    formats: tuple[str, ...] = ("png",),
) -> FigureMetadata:
    """Writes `<output_dir>/<figure_id>.<format>` for each requested
    format plus a `<figure_id>.json` metadata sidecar (Phase 14.5), and
    closes the figure. Never generates the figure itself — every caller
    in `genevra.artifacts.figures` builds `fig` from real, already-stored
    data first."""
    output_dir.mkdir(parents=True, exist_ok=True)
    files = []
    for fmt in formats:
        filename = f"{figure_id}.{fmt}"
        fig.savefig(output_dir / filename, format=fmt, bbox_inches="tight")
        files.append(filename)
    plt = require_matplotlib()
    plt.close(fig)

    metadata = FigureMetadata(
        figure_id=figure_id,
        experiment_id=experiment_id,
        data_source=data_source,
        metrics=metrics,
        analysis_version=analysis_version,
        seed_policy=seed_policy,
        creation_timestamp=datetime.now(UTC).isoformat(),
        git_commit=_git_commit(),
        parameters=parameters or {},
        caption=caption,
        limitations=limitations,
        files=tuple(files),
    )
    (output_dir / f"{figure_id}.json").write_text(json.dumps(metadata.to_dict(), indent=2))
    return metadata


__all__ = ["apply_style", "FigureMetadata", "save_figure", "require_matplotlib"]
