"""Application settings. Only the data folder differs between environments (architecture 8.2.6)."""

import os
from pathlib import Path

APP_NAME = "USPTO Patent Intelligence"

# Development sets this to a local, git-ignored folder; production leaves it unset.
DATA_FOLDER_VARIABLE = "PATENT_INTELLIGENCE_DATA"


def data_folder() -> Path:
    """Return the folder that holds the database and the log file."""
    override = os.environ.get(DATA_FOLDER_VARIABLE)
    if override:
        return Path(override)
    return Path.home() / "Library" / "Application Support" / APP_NAME
