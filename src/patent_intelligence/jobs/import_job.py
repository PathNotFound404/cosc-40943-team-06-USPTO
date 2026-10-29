"""The background job for one dropped file."""

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from patent_intelligence.ingestion import ImportSummary, import_file
from patent_intelligence.jobs.runner import ProgressCallback
from patent_intelligence.storage import Database


@dataclass(frozen=True)
class ImportJob:
    """Imports one file. Each dropped file is its own job, so one bad file does not stop
    the others (ROB-bad-input) and an interruption loses only the file in progress."""

    database: Database
    path: Path
    import_time: datetime

    def run(self, report_progress: ProgressCallback) -> ImportSummary:
        return import_file(self.database, self.path, self.import_time, report_progress)
