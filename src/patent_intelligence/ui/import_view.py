"""The Import view: drop target, progress bar, and in-app notices (UI-drag-and-drop,
USE-progress, FR-TASK-completion-notice)."""

from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QDragEnterEvent, QDropEvent
from PySide6.QtWidgets import QLabel, QListWidget, QProgressBar, QVBoxLayout, QWidget

from patent_intelligence.errors import AppError
from patent_intelligence.ingestion import ImportSummary
from patent_intelligence.jobs.import_job import ImportJob, ImportJobResult
from patent_intelligence.jobs.runner import JobRunner
from patent_intelligence.storage import Database


def _now() -> datetime:
    return datetime.now(UTC)


class ImportView(QWidget):
    def __init__(
        self,
        runner: JobRunner,
        database: Database,
        clock: Callable[[], datetime] = _now,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._runner = runner
        self._database = database
        self._clock = clock
        self.setAcceptDrops(True)

        self.instructions = QLabel("Drop weekly office action files here to import them.")
        self.instructions.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_label = QLabel("")
        self.notices = QListWidget()

        layout = QVBoxLayout(self)
        layout.addWidget(self.instructions, stretch=1)
        layout.addWidget(self.progress_label)
        layout.addWidget(self.progress_bar)
        layout.addWidget(self.notices, stretch=1)

        runner.progress.connect(self._show_progress)
        runner.finished.connect(self._show_finished)
        runner.failed.connect(self._show_failed)

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent) -> None:
        paths = [Path(url.toLocalFile()) for url in event.mimeData().urls() if url.isLocalFile()]
        self.on_files_dropped(paths)
        event.acceptProposedAction()

    def on_files_dropped(self, paths: list[Path]) -> None:
        """Queue one import per file, in the order dropped (UC-FEAT-decompile-files 1-2).

        The view checks only that a file was chosen; Ingestion decides what is valid (8.2.5).
        """
        files = [path for path in paths if path.is_file()]
        if not files:
            self.notices.addItem("Nothing to import: drop one or more files, not a folder.")
            return
        for path in files:
            self._runner.submit(ImportJob(self._database, path, self._clock()))

    def _show_progress(self, fraction: float, message: str) -> None:
        self.progress_bar.setValue(round(fraction * 100))
        self.progress_label.setText(message)

    def _show_finished(self, result: object) -> None:
        if isinstance(result, ImportJobResult):
            self.notices.addItem(import_notice(result.import_summary))
            if notice := cleaning_notice(result):
                self.notices.addItem(notice)

    def _show_failed(self, error: AppError) -> None:
        self.progress_label.setText("")
        self.progress_bar.setValue(0)
        self.notices.addItem(error.message)


def import_notice(summary: ImportSummary) -> str:
    """The completion notice: records loaded and rejected (steps 7 and 5a2)."""
    if summary.already_imported:
        return f"{summary.file_name} has already been imported. Nothing was changed."
    notice = (
        f"{summary.file_name} imported: {summary.records_loaded:,} records loaded, "
        f"{summary.records_rejected:,} rejected."
    )
    if summary.rejected_by_reason:
        reasons = "; ".join(
            f"{reason}: {count:,}" for reason, count in summary.rejected_by_reason.items()
        )
        notice += f" Rejected because of {reasons}."
    if summary.duplicate_records:
        notice += (
            f" {summary.duplicate_records:,} of the loaded records have an id that was already "
            "stored; charts use the newest copy."
        )
    return notice


def cleaning_notice(result: ImportJobResult) -> str | None:
    """Ready for charts (UC-FEAT-clean-data step 4), or why not (1a1, 2a2, 3a1). None when
    cleaning did not run because the file was already imported."""
    if result.cleaning_error is not None:
        return result.cleaning_error.message
    if result.staged_summary is None:
        return None
    staged = result.staged_summary
    return (
        f"Ready for charts: {staged.office_actions_staged:,} office actions and "
        f"{staged.rejections_staged:,} rejections staged."
    )
