"""The rotating log file (architecture 8.2.7).

Callers log counts and outcomes only: never office action text, whole records,
or examiner numbers. Nothing is sent anywhere (SEC-no-telemetry).
"""

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

LOG_FILE_NAME = "patent-intelligence.log"


def configure_logging(data_folder: Path) -> Path:
    """Send INFO and above to a rotating file in the data folder; return its path."""
    log_folder = data_folder / "logs"
    log_folder.mkdir(parents=True, exist_ok=True)
    log_path = log_folder / LOG_FILE_NAME
    handler = RotatingFileHandler(log_path, maxBytes=5_000_000, backupCount=3, encoding="utf-8")
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s"))
    root = logging.getLogger()
    root.setLevel(logging.INFO)
    root.addHandler(handler)
    return log_path
