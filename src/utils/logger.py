"""Logging helpers for the per-title encoding demo."""

from __future__ import annotations

import logging
from pathlib import Path


def setup_logging(level: int = logging.INFO, log_file: Path | None = None) -> logging.Logger:
    logger = logging.getLogger("per_title")
    if logger.handlers:
        return logger
    logger.setLevel(level)
    fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s", "%H:%M:%S")
    stream = logging.StreamHandler()
    stream.setFormatter(fmt)
    logger.addHandler(stream)
    if log_file is not None:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setFormatter(fmt)
        logger.addHandler(file_handler)
    logger.propagate = False
    return logger
