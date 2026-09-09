"""Experiment logging setup.

Thin wrapper around stdlib `logging` configured for research runs: a
timestamped, leveled format on stderr. Experiment scripts should call
`configure_logging` once at startup and then use `logging.getLogger(__name__)`
as usual.
"""

from __future__ import annotations

import logging
import sys


def configure_logging(level: int = logging.INFO) -> None:
    """Configure root logging for a GENEVRA run. Safe to call multiple times."""
    logging.basicConfig(
        level=level,
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
        stream=sys.stderr,
        force=True,
    )
