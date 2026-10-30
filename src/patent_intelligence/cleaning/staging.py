"""Building the staged dataset from the raw records (UC-FEAT-clean-data)."""

import logging
from dataclasses import dataclass

import duckdb

from patent_intelligence.cleaning.errors import (
    CleaningFailedError,
    MissingColumnsError,
    NoRawDataError,
)
from patent_intelligence.storage import Database

log = logging.getLogger(__name__)

# One copy per record id: the latest systemLastModifiedTimestamp, with a missing or unparsable
# one counting as the oldest; on a tie the later import, then the later line
# (docs/design/intake.md, duplicate records). Timestamps are UTC as supplied (8.2.2).
_CHOSEN_COPIES = """
    SELECT * FROM raw_office_action
    QUALIFY row_number() OVER (
        PARTITION BY id
        ORDER BY try_cast(systemLastModifiedTimestamp AS TIMESTAMP) DESC NULLS LAST,
            import_id DESC, line_number DESC
    ) = 1
"""

# The staged views, replaced on every run. Values are renamed and typed, never filled in or
# changed (BR-no-data-alteration): a value that does not parse is left empty.
STAGED_VIEWS = {
    "staged_office_action": f"""
        SELECT
            id AS record_id,
            patentApplicationNumber AS application_number,
            groupArtUnitNumber AS art_unit,
            workGroup AS work_group,
            techCenter AS technology_center,
            examinerEmployeeNumber AS examiner_number,
            documentCode AS document_code,
            try_cast(submissionDate AS TIMESTAMP) AS submission_date,
            try_cast(filingDate AS TIMESTAMP) AS filing_date,
            import_id
        FROM ({_CHOSEN_COPIES})
    """,
    "staged_rejection": f"""
        SELECT
            id AS record_id,
            json_extract_string(entry, '$.type') AS rejection_type,
            json_extract_string(entry, '$.label') AS rejection_label,
            import_id
        FROM ({_CHOSEN_COPIES}), unnest(json_extract(rejections, '$[*]')) AS entries(entry)
    """,
}

# The columns charts need, checked after the views are built (step 3).
REQUIRED_COLUMNS = {
    "staged_office_action": (
        "record_id",
        "application_number",
        "art_unit",
        "work_group",
        "technology_center",
        "examiner_number",
        "document_code",
        "submission_date",
        "filing_date",
        "import_id",
    ),
    "staged_rejection": ("record_id", "rejection_type", "rejection_label", "import_id"),
}


@dataclass(frozen=True)
class StagedSummary:
    """The outcome of one cleaning run: rows in each staged view."""

    office_actions_staged: int
    rejections_staged: int


def build_staged_dataset(database: Database) -> StagedSummary:
    """Replace the staged views over the raw records, in one transaction.

    Run on the Job Runner thread after an import. Raises NoRawDataError (1a),
    CleaningFailedError (2a), or MissingColumnsError (3a); in every case the raw records and
    the previous staged views are left as they were.
    """
    cursor = database.cursor()
    try:
        (raw_records,) = cursor.execute("SELECT count(*) FROM raw_office_action").fetchone()
        if raw_records == 0:
            raise NoRawDataError()
        log.info("Building the staged dataset from %d raw records", raw_records)
        try:
            with database.transaction(cursor):
                for name, query in STAGED_VIEWS.items():
                    cursor.execute(f"CREATE OR REPLACE VIEW {name} AS {query}")
                missing = _missing_columns(cursor)
                if missing:
                    log.warning("The staged dataset is missing columns: %s", ", ".join(missing))
                    raise MissingColumnsError(missing)
                (office_actions,) = cursor.execute(
                    "SELECT count(*) FROM staged_office_action"
                ).fetchone()
                (rejections,) = cursor.execute("SELECT count(*) FROM staged_rejection").fetchone()
        except duckdb.Error as error:
            log.exception("Building the staged dataset failed; it was rolled back")
            raise CleaningFailedError() from error
    finally:
        cursor.close()

    log.info(
        "Built the staged dataset: %d office actions, %d rejections", office_actions, rejections
    )
    return StagedSummary(office_actions, rejections)


def _missing_columns(cursor: duckdb.DuckDBPyConnection) -> list[str]:
    built = set(
        cursor.execute(
            "SELECT table_name, column_name FROM information_schema.columns "
            "WHERE table_name IN (SELECT unnest(?::TEXT[]))",
            [list(REQUIRED_COLUMNS)],
        ).fetchall()
    )
    return [
        f"{view}.{column}"
        for view, columns in REQUIRED_COLUMNS.items()
        for column in columns
        if (view, column) not in built
    ]
