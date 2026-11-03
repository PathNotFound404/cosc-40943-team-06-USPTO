"""Failures that stop the source records from being shown. Nothing is ever changed."""

from patent_intelligence.errors import AppError


class SourceUnavailableError(AppError):
    """The records behind a chart no longer exist or no longer add up to it
    (UC-FEAT-verify-source 2a)."""

    def __init__(self) -> None:
        super().__init__(
            "The source data for this visualization is no longer available. "
            "Create the visualization again to see its source records."
        )


class SourceLookupFailedError(AppError):
    """The source records could not be read (the use case's "Failure handling")."""

    def __init__(self) -> None:
        super().__init__(
            "The source records could not be read. Details were written to the log file."
        )
