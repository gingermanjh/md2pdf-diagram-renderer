from __future__ import annotations

import logging

_LOGGER_NAME = "md2pdf"


def configure_logging(verbose: bool) -> logging.Logger:
    logger = logging.getLogger(_LOGGER_NAME)
    level = logging.DEBUG if verbose else logging.INFO
    logger.setLevel(level)

    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter("[%(levelname)s] %(message)s")
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    for handler in logger.handlers:
        handler.setLevel(level)

    return logger
