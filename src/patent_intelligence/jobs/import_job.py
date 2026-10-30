"""The background job for one dropped file: import it, then build the staged dataset."""

import logging
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from patent_intelligence.cleaning import StagedSummary, build_staged_dataset
from patent_intelligence.errors import AppError
from patent_intelligence.ingestion import ImportSummary, import_file
from patent_intelligence.jobs.runner import ProgressCallback
from patent_intelligence.storage import Database

log = logging.getLogger(__name__)


@dataclass(frozen=True)
class ImportJobResult:
    """The import's outcome and the cleaning run's. The import is committed before cleaning
    starts, so a cleaning failure is reported alongside it rather than replacing it."""

    import_summary: ImportSummary
    staged_summary: StagedSummary | None = None
    cleaning_error: AppError | None = None


@dataclass(frozen=True)
class ImportJob:
    """Imports one file. Each dropped file is its own job, so one bad file does not stop
    the others (ROB-bad-input) and an interruption loses only the file in progress."""

    database: Database
    path: Path
    import_time: datetime

    def run(self, report_progress: ProgressCallback) -> ImportJobResult:
        summary = import_file(self.database, self.path, self.import_time, report_progress)
        if summary.already_imported:
            return ImportJobResult(summary)
        # UC-FEAT-clean-data is triggered by the finished import.
        report_progress(1.0, f"Preparing {summary.file_name} for charts")
        try:
            staged = build_staged_dataset(self.database)
        except AppError as error:
            log.warning("Cleaning after %s failed: %s", summary.file_name, type(error).__name__)
            return ImportJobResult(summary, cleaning_error=error)
        return ImportJobResult(summary, staged)
