from datetime import date, datetime, timedelta
from pathlib import Path

import pytest

from patent_intelligence import storage
from patent_intelligence.cleaning import build_staged_dataset
from patent_intelligence.ingestion import import_file
from tests.ingestion.conftest import (
    FIXTURE,
    IMPORT_TIME,
    fixture_records,
    no_progress,
    write_records,
)

# Counted by hand from tests/fixtures/office_actions_20.jsonl (the oracle for the main flow).
EXPECTED_COUNTS = {
    ("office-actions-by-document-code", ()): {"CTNF": 11, "CTFR": 9},
    ("office-actions-by-technology-center", ()): {
        "1600": 8,
        "3700": 5,
        "3600": 2,
        "1700": 1,
        "2600": 1,
        "2800": 1,
        "2900": 1,
        "3900": 1,
    },
    ("rejections-by-type", ()): {
        "103": 9,
        "112": 5,
        "101": 3,
        "102": 1,
        "Other": 1,
        None: 1,
    },
    ("office-actions-by-art-unit", (("technology_center", "3700"),)): {
        "3783": 2,
        "3761": 1,
        "3773": 1,
        "3798": 1,
    },
}
# Each Technology Center's office actions; every fixture record has one rejection entry, so
# its rejection entries too.
_BY_TECHNOLOGY_CENTER = EXPECTED_COUNTS[("office-actions-by-technology-center", ())]
EXPECTED_COUNTS[("rejections-by-technology-center-and-type", ())] = _BY_TECHNOLOGY_CENTER
EXPECTED_COUNTS[("office-actions-by-technology-center-and-document-code", ())] = (
    _BY_TECHNOLOGY_CENTER
)

# Two-way metrics: count per (Technology Center, series), counted by hand from the fixture.
EXPECTED_BREAKDOWN = {
    "rejections-by-technology-center-and-type": {
        ("1600", "101"): 1,
        ("1600", "103"): 3,
        ("1600", "112"): 4,
        ("1700", "103"): 1,
        ("2600", "103"): 1,
        ("2800", None): 1,
        ("2900", "Other"): 1,
        ("3600", "101"): 2,
        ("3700", "102"): 1,
        ("3700", "103"): 3,
        ("3700", "112"): 1,
        ("3900", "103"): 1,
    },
    "office-actions-by-technology-center-and-document-code": {
        ("1600", "CTFR"): 4,
        ("1600", "CTNF"): 4,
        ("1700", "CTNF"): 1,
        ("2600", "CTFR"): 1,
        ("2800", "CTFR"): 1,
        ("2900", "CTNF"): 1,
        ("3600", "CTNF"): 2,
        ("3700", "CTFR"): 3,
        ("3700", "CTNF"): 2,
        ("3900", "CTNF"): 1,
    },
}


def staged(database) -> None:
    """Import the 20-record fixture and build the staged dataset from it."""
    import_file(database, FIXTURE, IMPORT_TIME, no_progress)
    build_staged_dataset(database)


# Two imports over two calendar weeks (6b). Import 1 is the fixture (submitted 2026-10-13 to
# 2026-10-16, the week of Monday 2026-10-12). Import 2 holds copies of fixture records 0-4
# under new ids, submitted 7 days later (week of 2026-10-19), and a newer copy of record 5
# (3700, CTNF) with its Submission Date unchanged, so record 5 is staged from import 2 but
# stays in the first week.
SECOND_IMPORT_TIME = IMPORT_TIME + timedelta(days=7)
WEEK_1, WEEK_2 = date(2026, 10, 12), date(2026, 10, 19)
# Office actions by Document Code, counted by hand, for each choice of weeks.
TWO_WEEK_DOCUMENT_CODES = {
    "all": {"CTNF": 14, "CTFR": 11},
    "import 1": {"CTNF": 10, "CTFR": 9},
    "import 2": {"CTNF": 4, "CTFR": 2},
    "week 1": {"CTNF": 11, "CTFR": 9},
    "week 2": {"CTNF": 3, "CTFR": 2},
}
# Rejections by type in the week of 2026-10-19: fixture records 0-4.
WEEK_2_REJECTIONS = {"103": 2, "112": 1, "Other": 1, None: 1}


def _second_week(records: list[dict]) -> list[dict]:
    later = []
    for record in records[:5]:
        copy = dict(record)
        copy["id"] = record["id"] + "-week-2"
        submitted = datetime.fromisoformat(record["submissionDate"]) + timedelta(days=7)
        copy["submissionDate"] = submitted.strftime("%Y-%m-%dT%H:%M:%S.000Z")
        later.append(copy)
    newer = dict(records[5])
    newer["systemLastModifiedTimestamp"] = "2026-10-25T00:00:00.000Z"
    return [*later, newer]


def staged_two_weeks(database, folder: Path) -> None:
    import_file(database, FIXTURE, IMPORT_TIME, no_progress)
    second = write_records(folder / "week_2026-10-25.jsonl", _second_week(fixture_records()))
    import_file(database, second, SECOND_IMPORT_TIME, no_progress)
    build_staged_dataset(database)


@pytest.fixture
def two_weeks_database(database, tmp_path: Path):
    staged_two_weeks(database, tmp_path)
    return database


@pytest.fixture
def database(tmp_path: Path):
    database = storage.open(tmp_path / "data")
    yield database
    database.close()


@pytest.fixture
def staged_database(database):
    staged(database)
    return database
