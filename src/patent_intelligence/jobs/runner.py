"""Runs jobs one at a time on one background thread and reports through Qt signals."""

import logging
import queue
import threading
from collections.abc import Callable
from typing import Protocol

from PySide6.QtCore import QObject, Signal

from patent_intelligence.errors import AppError

log = logging.getLogger(__name__)

ProgressCallback = Callable[[float, str], None]


class Job(Protocol):
    def run(self, report_progress: ProgressCallback) -> object:
        """Do the work, calling `report_progress(fraction, message)` as it goes."""
        ...


class JobRunner(QObject):
    """Runs submitted jobs in the order submitted; a job submitted while one runs waits its turn.

    The signals are emitted from the background thread; Qt queues them to slots on the UI thread.
    `failed` always carries an `AppError`, so the UI shows its message and never a stack trace
    (architecture 8.2.1).
    """

    progress = Signal(float, str)
    finished = Signal(object)
    failed = Signal(object)

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._jobs: queue.Queue[Job | None] = queue.Queue()
        self._thread = threading.Thread(target=self._work, name="job-runner", daemon=True)
        self._thread.start()

    def submit(self, job: Job) -> None:
        self._jobs.put(job)

    def shutdown(self, wait: bool = True) -> None:
        """Stop after the jobs already submitted. Quitting does not wait: an unfinished
        import's transaction is never committed, so it is rolled back (ROB-resume)."""
        self._jobs.put(None)
        if wait:
            self._thread.join()

    def _work(self) -> None:
        while (job := self._jobs.get()) is not None:
            try:
                result = job.run(self.progress.emit)
            except AppError as error:
                log.warning("%s failed: %s", type(job).__name__, type(error).__name__)
                self.failed.emit(error)
            except Exception:
                log.exception("%s failed unexpectedly", type(job).__name__)
                self.failed.emit(
                    AppError("Something went wrong. Details were written to the log file.")
                )
            else:
                self.finished.emit(result)
