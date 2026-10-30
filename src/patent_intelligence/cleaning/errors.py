"""Failures that leave the imported records unstaged. The raw records are never changed."""

from patent_intelligence.errors import AppError


class NoRawDataError(AppError):
    """There are no raw records to build the staged dataset from (UC-FEAT-clean-data 1a)."""

    def __init__(self) -> None:
        super().__init__("There is no data to clean. Import a weekly file first.")


class CleaningFailedError(AppError):
    """Building the staged dataset failed and was rolled back (2a)."""

    def __init__(self) -> None:
        super().__init__(
            "Cleaning failed. The imported records were kept unchanged, but they are not ready "
            "for charts. Details were written to the log file."
        )


class MissingColumnsError(AppError):
    """The staged dataset lacks columns charts need, so it was not staged (3a)."""

    def __init__(self, missing: list[str]) -> None:
        super().__init__(
            f"Cleaning did not produce the columns charts need (missing {', '.join(missing)}). "
            "The imported records were kept unchanged, but they are not ready for charts."
        )
        self.missing = missing
