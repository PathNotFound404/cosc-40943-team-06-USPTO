"""Importing one weekly file into the raw tables (UC-FEAT-decompile-files)."""

import hashlib
import logging
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path

import duckdb

from patent_intelligence import __version__
from patent_intelligence.ingestion.errors import LayoutMismatchError, UnreadableFileError
from patent_intelligence.ingestion.layout import (
    EXPECTED_FIELDS,
    JSON_FIELDS,
    json_values_sql,
    rejection_reason_sql,
)
from patent_intelligence.ingestion.readers import JsonLinesReader
from patent_intelligence.storage import Database

log = logging.getLogger(__name__)

ProgressCallback = Callable[[float, str], None]

_HASH_CHUNK_BYTES = 8 * 1024 * 1024
_LINES = "import_line"
_CHECKED = "import_checked_line"


@dataclass(frozen=True)
class ImportSummary:
    """The outcome of one import. `already_imported` means nothing was written."""

    import_id: int
    file_name: str
    records_loaded: int
    records_rejected: int
    rejected_by_reason: dict[str, int] = field(default_factory=dict)
    already_imported: bool = False


def import_file(
    database: Database, path: Path, import_time: datetime, report_progress: ProgressCallback
) -> ImportSummary:
    """Check a weekly file and load its records unchanged, in one transaction.

    Run on the Job Runner thread, never the UI thread. `import_time` is passed in (8.2.2).
    Raises UnsupportedFileError or LayoutMismatchError (3a) and UnreadableFileError (4a);
    in every case nothing from the file is stored. Rejected records (5a) are counted in
    the summary, not raised.
    """
    path = Path(path)
    file_name = path.name
    reader = JsonLinesReader()
    report_progress(0.0, f"Checking {file_name}")
    reader.check_layout(path)
    content_hash = _hash_file(path, report_progress)

    cursor = database.cursor()
    try:
        existing = cursor.execute(
            "SELECT import_id FROM import_log WHERE content_hash = ?", [content_hash]
        ).fetchone()
        if existing is not None:
            log.info(
                "%s was already imported as import %d; nothing changed", file_name, existing[0]
            )
            report_progress(1.0, f"{file_name} was already imported")
            return ImportSummary(existing[0], file_name, 0, 0, already_imported=True)

        with database.transaction(cursor):
            report_progress(0.3, f"Reading {file_name}")
            reader.stage_lines(cursor, path, _LINES)
            report_progress(0.5, f"Checking the records in {file_name}")
            _refuse_unreadable_lines(cursor, file_name)
            _refuse_unexpected_fields(cursor, file_name)
            cursor.execute(
                f"CREATE OR REPLACE TEMP TABLE {_CHECKED} AS "
                f"SELECT line_number, line, {rejection_reason_sql('line')} AS reason FROM {_LINES}"
            )
            loaded, rejected = cursor.execute(
                f"SELECT count(*) FILTER (reason = ''), count(*) FILTER (reason <> '') "
                f"FROM {_CHECKED}"
            ).fetchone()

            report_progress(0.7, f"Storing the records from {file_name}")
            (import_id,) = cursor.execute("SELECT nextval('import_id_sequence')").fetchone()
            cursor.execute(
                "INSERT INTO import_log VALUES (?, ?, ?, ?, ?, ?, ?)",
                [
                    import_id,
                    file_name,
                    content_hash,
                    _as_utc(import_time),
                    loaded,
                    rejected,
                    __version__,
                ],
            )
            cursor.execute(_insert_raw_records_sql(), [import_id])
            cursor.execute(
                "INSERT INTO rejected_record "
                f"SELECT ?, line_number, reason, line FROM {_CHECKED} WHERE reason <> ''",
                [import_id],
            )
            rejected_by_reason = dict(
                cursor.execute(
                    f"SELECT reason, count(*) FROM {_CHECKED} WHERE reason <> '' "
                    "GROUP BY reason ORDER BY reason"
                ).fetchall()
            )
            cursor.execute(f"DROP TABLE {_CHECKED}; DROP TABLE {_LINES}")
    finally:
        cursor.close()

    log.info(
        "Imported %s as import %d: %d records loaded, %d rejected",
        file_name,
        import_id,
        loaded,
        rejected,
    )
    if rejected:
        log.warning("Rejected records in %s by reason: %s", file_name, rejected_by_reason)
    report_progress(1.0, f"Imported {file_name}")
    return ImportSummary(import_id, file_name, loaded, rejected, rejected_by_reason)


def _hash_file(path: Path, report_progress: ProgressCallback) -> str:
    total = max(path.stat().st_size, 1)
    digest = hashlib.sha256()
    done = 0
    with path.open("rb") as file:
        while chunk := file.read(_HASH_CHUNK_BYTES):
            digest.update(chunk)
            done += len(chunk)
            report_progress(0.3 * done / total, f"Checking {path.name}")
    return digest.hexdigest()


def _refuse_unreadable_lines(cursor: duckdb.DuckDBPyConnection, file_name: str) -> None:
    (first_bad_line,) = cursor.execute(
        f"SELECT min(line_number) FROM {_LINES} "
        "WHERE line IS NULL OR NOT json_valid(line) OR json_type(line) <> 'OBJECT'"
    ).fetchone()
    if first_bad_line is not None:
        raise UnreadableFileError(file_name, first_bad_line)


def _refuse_unexpected_fields(cursor: duckdb.DuckDBPyConnection, file_name: str) -> None:
    """Catch a field the layout sample did not see, so no value is silently dropped."""
    rows = cursor.execute(
        f"SELECT DISTINCT unnest(json_keys(line)) AS name FROM {_LINES} "
        "EXCEPT SELECT unnest(?::TEXT[]) ORDER BY name",
        [list(EXPECTED_FIELDS)],
    ).fetchall()
    if rows:
        raise LayoutMismatchError(file_name, [], [name for (name,) in rows])


def _insert_raw_records_sql() -> str:
    text_fields = tuple(name for name in EXPECTED_FIELDS if name not in JSON_FIELDS)
    json_fields = tuple(name for name in EXPECTED_FIELDS if name in JSON_FIELDS)
    columns = [
        f"json_values[{json_fields.index(name) + 1}]"
        if name in JSON_FIELDS
        else f"text_values[{text_fields.index(name) + 1}]"
        for name in EXPECTED_FIELDS
    ]
    return (
        f"INSERT INTO raw_office_action (import_id, line_number, {', '.join(EXPECTED_FIELDS)}) "
        f"SELECT ?, line_number, {', '.join(columns)} FROM ("
        f"SELECT line_number, {json_values_sql('line', text_fields)} AS text_values, "
        f"{json_values_sql('line', json_fields, as_text=False)} AS json_values "
        f"FROM {_CHECKED} WHERE reason = '')"
    )


def _as_utc(moment: datetime) -> datetime:
    """Stored as UTC without a zone (8.2.2); a moment without a zone is taken as UTC."""
    if moment.tzinfo is None:
        return moment
    return moment.astimezone(UTC).replace(tzinfo=None)
