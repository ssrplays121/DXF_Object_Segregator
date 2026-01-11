"""Logging configuration and utilities."""

import logging
import logging.handlers
from pathlib import Path


def setup_logging(log_level=logging.INFO, log_file=None):
    """
    Setup logging configuration.

    Args:
        log_level: Logging level (default: INFO).
        log_file: Optional log file path.
    """
    logger = logging.getLogger("dxf_object_segregator")
    logger.setLevel(log_level)

    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File handler
    if log_file:
        file_handler = logging.handlers.RotatingFileHandler(
            log_file, maxBytes=10485760, backupCount=5
        )
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


def get_logger(name):
    """Get a logger instance."""
    return logging.getLogger(f"dxf_object_segregator.{name}")
