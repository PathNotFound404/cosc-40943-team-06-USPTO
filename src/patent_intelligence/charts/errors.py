"""Failures that stop charts from being exported. The stored data is never changed."""

from pathlib import Path

from patent_intelligence.errors import AppError


class FolderNotWritableError(AppError):
    """The chosen folder cannot be written to, or has no space left (UC-FEAT-export-visuals
    4a)."""

    def __init__(self, folder: Path) -> None:
        super().__init__(
            f"The visualizations cannot be saved in {folder}: the folder does not exist, "
            "cannot be written to, or has no space left. Choose a different folder."
        )
        self.folder = folder
