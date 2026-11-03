from pathlib import Path

import pytest

from tests.analytics.conftest import database, staged_database, two_weeks_database  # noqa: F401


@pytest.fixture
def folder(tmp_path: Path) -> Path:
    """An empty folder to export to, apart from the test's database."""
    folder = tmp_path / "exports"
    folder.mkdir()
    return folder
