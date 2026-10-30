from pathlib import Path

import pytest

from patent_intelligence import storage
from patent_intelligence.cleaning import build_staged_dataset
from patent_intelligence.ingestion import import_file
from tests.ingestion.conftest import FIXTURE, IMPORT_TIME, no_progress

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


@pytest.fixture
def database(tmp_path: Path):
    database = storage.open(tmp_path / "data")
    yield database
    database.close()


@pytest.fixture
def staged_database(database):
    staged(database)
    return database
