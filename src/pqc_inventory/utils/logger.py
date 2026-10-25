"""
Centralized logging system for the TLS/PQC pipeline.

This module configures logging once per process and ensures all project
modules inherit the same handlers. It prevents duplicate logs, handler
duplication, and Windows file-locking issues.

Debug mode is controlled by the pipeline using:
    PIPELINE_DEBUG=1 -> DEBUG logging
    PIPELINE_DEBUG=0 -> INFO logging

Log outputs:
    logs/audit.log -> INFO and above (audit trail)
    logs/debug.log -> DEBUG and above (diagnostics)
"""

import logging
import os
from pathlib import Path
from logging.handlers import RotatingFileHandler

LOG_DIR = Path("logs")

_STATE = {"initialized": False}


def init_logging() -> None:
    """
    Initialize logging once for the entire pipeline.
    Child loggers inherit handlers without duplication.
    """
    if _STATE["initialized"]:
        return

    LOG_DIR.mkdir(exist_ok=True)

    debug_mode = os.getenv("PIPELINE_DEBUG") == "1"
    console_level = logging.DEBUG if debug_mode else logging.INFO

    # Root logger must always be DEBUG so debug.log receives all messages
    root = logging.getLogger()
    root.setLevel(logging.DEBUG)

    formatter = logging.Formatter(
        "[%(asctime)s] %(levelname)-8s - %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Audit log (INFO+), rotating to prevent disk exhaustion
    audit_handler = RotatingFileHandler(
        LOG_DIR / "audit.log",
        maxBytes=10_000_000,  # 10 MB
        backupCount=5,
        encoding="utf-8",
    )
    audit_handler.setLevel(logging.INFO)
    audit_handler.setFormatter(formatter)
    root.addHandler(audit_handler)

    # Debug log (DEBUG+), rotating
    debug_handler = RotatingFileHandler(
        LOG_DIR / "debug.log",
        maxBytes=10_000_000,
        backupCount=5,
        encoding="utf-8",
    )
    debug_handler.setLevel(logging.DEBUG)
    debug_handler.setFormatter(formatter)
    root.addHandler(debug_handler)

    # Console output (INFO or DEBUG depending on pipeline flag)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(console_level)
    console_handler.setFormatter(formatter)
    root.addHandler(console_handler)

    _STATE["initialized"] = True


def get_logger(name: str) -> logging.Logger:
    """
    Return a child logger. Handlers are attached only to the root.
    """
    init_logging()
    return logging.getLogger(name)
