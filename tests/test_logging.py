import logging

from genevra.utils.logging import configure_logging


def test_configure_logging_sets_level() -> None:
    configure_logging(level=logging.DEBUG)
    assert logging.getLogger().level == logging.DEBUG

    configure_logging(level=logging.WARNING)
    assert logging.getLogger().level == logging.WARNING
