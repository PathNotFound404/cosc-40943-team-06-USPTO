import json
from datetime import UTC, datetime
from pathlib import Path

import pytest

from patent_intelligence import storage

FIXTURE = Path(__file__).parent.parent / "fixtures" / "office_actions_20.jsonl"
IMPORT_TIME = datetime(2026, 10, 28, 15, 30, tzinfo=UTC)


def fixture_records() -> list[dict]:
    with FIXTURE.open(encoding="utf-8") as file:
        return [json.loads(line) for line in file]


def write_records(path: Path, records: list[dict]) -> Path:
    with path.open("w", encoding="utf-8", newline="\n") as file:
        for record in records:
            file.write(json.dumps(record, ensure_ascii=False, separators=(",", ":")) + "\n")
    return path


def no_progress(fraction: float, message: str) -> None:
    pass


def counts(database) -> dict[str, int]:
    cursor = database.cursor()
    return {
        table: cursor.execute(f"SELECT count(*) FROM {table}").fetchone()[0]
        for table in ("import_log", "raw_office_action", "rejected_record")
    }


@pytest.fixture
def database(tmp_path: Path):
    database = storage.open(tmp_path / "data")
    yield database
    database.close()
