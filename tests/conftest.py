"""Shared test helpers. Qt runs offscreen so the tests need no display."""

import os
import time
from collections.abc import Callable

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest  # noqa: E402
from PySide6.QtWidgets import QApplication  # noqa: E402


@pytest.fixture(scope="session")
def qt_app() -> QApplication:
    return QApplication.instance() or QApplication([])


def wait_until(condition: Callable[[], bool], timeout: float = 30.0) -> None:
    """Process Qt events until `condition()` holds, so queued signals are delivered."""
    deadline = time.monotonic() + timeout
    while not condition():
        if time.monotonic() > deadline:
            raise AssertionError("Timed out waiting for the condition")
        QApplication.processEvents()
        time.sleep(0.01)
