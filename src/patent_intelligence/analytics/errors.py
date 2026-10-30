"""Failures that stop a visualization from being created. The stored data is never changed."""

from patent_intelligence.errors import AppError


class StagedDataMissingError(AppError):
    """There is no staged dataset to chart (UC-FEAT-create-visuals 2a)."""

    def __init__(self) -> None:
        super().__init__(
            "Visualizations cannot be created until the data is cleaned and staged for charts."
        )


class MetricFailedError(AppError):
    """One metric could not be counted or drawn (5a); the others go on."""

    def __init__(self, metric_name: str) -> None:
        super().__init__(
            f"The visualization {metric_name} could not be created. "
            "Details were written to the log file."
        )
        self.metric_name = metric_name
