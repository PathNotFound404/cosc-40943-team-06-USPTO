import logging
import threading

import pytest

from patent_intelligence.errors import AppError
from patent_intelligence.jobs.runner import JobRunner
from tests.conftest import wait_until


class RecordingJob:
    def __init__(self, name: str, log: list[str], gate: threading.Event | None = None) -> None:
        self.name = name
        self.log = log
        self.gate = gate

    def run(self, report_progress):
        self.log.append(f"start {self.name}")
        report_progress(0.5, f"half of {self.name}")
        if self.gate is not None:
            self.gate.wait(5)
        self.log.append(f"end {self.name}")
        return self.name


class FailingJob:
    def __init__(self, error: Exception) -> None:
        self.error = error

    def run(self, report_progress):
        raise self.error


@pytest.fixture
def runner(qt_app):
    runner = JobRunner()
    yield runner
    runner.shutdown()


def collect(runner: JobRunner) -> dict[str, list]:
    seen: dict[str, list] = {"progress": [], "finished": [], "failed": []}
    runner.progress.connect(lambda fraction, message: seen["progress"].append((fraction, message)))
    runner.finished.connect(seen["finished"].append)
    runner.failed.connect(seen["failed"].append)
    return seen


def test_jobs_run_one_at_a_time_in_the_order_submitted(runner: JobRunner) -> None:
    seen = collect(runner)
    log: list[str] = []
    gate = threading.Event()
    runner.submit(RecordingJob("first", log, gate))
    runner.submit(RecordingJob("second", log))
    wait_until(lambda: log == ["start first"])
    gate.set()
    wait_until(lambda: len(seen["finished"]) == 2)
    assert log == ["start first", "end first", "start second", "end second"]
    assert seen["finished"] == ["first", "second"]
    assert (0.5, "half of first") in seen["progress"]


def test_an_app_error_is_reported_through_failed_with_its_message(runner: JobRunner) -> None:
    seen = collect(runner)
    runner.submit(FailingJob(AppError("The file could not be read.")))
    wait_until(lambda: seen["failed"])
    assert seen["failed"][0].message == "The file could not be read."
    assert seen["finished"] == []


def test_an_unexpected_error_is_logged_with_its_trace_and_shown_without_one(
    runner: JobRunner, caplog: pytest.LogCaptureFixture
) -> None:
    seen = collect(runner)
    with caplog.at_level(logging.ERROR):
        runner.submit(FailingJob(ZeroDivisionError("boom")))
        wait_until(lambda: seen["failed"])
    error = seen["failed"][0]
    assert isinstance(error, AppError)
    assert "Traceback" not in error.message and "boom" not in error.message
    assert "Traceback" in caplog.text


def test_a_failed_job_does_not_stop_the_next(runner: JobRunner) -> None:
    seen = collect(runner)
    runner.submit(FailingJob(AppError("bad")))
    runner.submit(RecordingJob("after", []))
    wait_until(lambda: seen["finished"] == ["after"])
    assert len(seen["failed"]) == 1
