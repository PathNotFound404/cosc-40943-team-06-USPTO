from pathlib import Path

import pytest

from patent_intelligence import storage
from patent_intelligence.cleaning import StagedSummary
from patent_intelligence.cleaning.errors import NoRawDataError
from patent_intelligence.ingestion import import_file
from patent_intelligence.jobs.cleaning_job import CleaningJob
from tests.ingestion.conftest import FIXTURE, IMPORT_TIME, no_progress


@pytest.fixture
def database(tmp_path: Path):
    database = storage.open(tmp_path / "data")
    yield database
    database.close()


def test_cleaning_on_its_own_stages_the_imported_records(database) -> None:
    import_file(database, FIXTURE, IMPORT_TIME, no_progress)
    assert CleaningJob(database).run(no_progress) == StagedSummary(20, 20)


def test_cleaning_with_nothing_imported_says_so(database) -> None:
    with pytest.raises(NoRawDataError):
        CleaningJob(database).run(no_progress)
