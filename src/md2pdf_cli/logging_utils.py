from __future__ import annotations

import logging

_LOGGER_NAME = "md2pdf"


def configure_logging(verbose: bool) -> logging.Logger:
    logger = logging.getLogger(_LOGGER_NAME)
    level = logging.DEBUG if verbose else logging.INFO
    logger.setLevel(level)

    # Remove existing handlers to prevent duplicates on repeated calls
    for h in logger.handlers[:]:
        logger.removeHandler(h)

    handler = logging.StreamHandler()
    formatter = logging.Formatter("[%(levelname)s] %(message)s")
    handler.setFormatter(formatter)
    handler.setLevel(level)
    logger.addHandler(handler)

    # Prevent log propagation to root logger
    logger.propagate = False

    return logger
