"""The background job that builds the staged dataset on its own, when the user chooses to clean
the data from the Visualizations view (UC-FEAT-create-visuals 2a2)."""

from dataclasses import dataclass

from patent_intelligence.cleaning import StagedSummary, build_staged_dataset
from patent_intelligence.jobs.runner import ProgressCallback
from patent_intelligence.storage import Database


@dataclass(frozen=True)
class CleaningJob:
    database: Database

    def run(self, report_progress: ProgressCallback) -> StagedSummary:
        report_progress(0.0, "Preparing the imported data for charts")
        summary = build_staged_dataset(self.database)
        report_progress(1.0, "Prepared the imported data for charts")
        return summary
