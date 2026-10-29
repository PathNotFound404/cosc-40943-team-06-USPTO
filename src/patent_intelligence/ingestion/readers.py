"""One reader per file layout (RISK-format-drift). Release 1.0 reads JSON lines only.

A reader opens only the path it is given, read-only, and parses it as data (8.1).
"""

import json
from dataclasses import dataclass
from itertools import islice
from pathlib import Path

import duckdb

from patent_intelligence.ingestion.errors import (
    LayoutMismatchError,
    UnreadableFileError,
    UnsupportedFileError,
)
from patent_intelligence.ingestion.layout import compare_field_names

LAYOUT_SAMPLE_SIZE = 100


@dataclass(frozen=True)
class LayoutCheck:
    records_sampled: int
    field_names: frozenset[str]


class JsonLinesReader:
    """One JSON office action record per line (SRS 7.2)."""

    def check_layout(self, path: Path) -> LayoutCheck:
        """Compare the field names of the first records with the expected layout.

        Raises UnsupportedFileError, LayoutMismatchError, or UnreadableFileError.
        """
        try:
            with path.open("r", encoding="utf-8") as file:
                lines = list(islice(file, LAYOUT_SAMPLE_SIZE))
        except UnicodeDecodeError as error:
            raise UnsupportedFileError(path.name, "it is not a text file") from error
        except OSError as error:
            raise UnreadableFileError(path.name, None) from error
        if not lines:
            raise UnsupportedFileError(path.name, "it is empty")

        field_names: set[str] = set()
        for line_number, line in enumerate(lines, start=1):
            try:
                record = json.loads(line)
            except json.JSONDecodeError as error:
                if line_number == 1:
                    raise UnsupportedFileError(
                        path.name, "its first line is not a JSON record"
                    ) from error
                raise UnreadableFileError(path.name, line_number) from error
            if not isinstance(record, dict):
                raise UnsupportedFileError(path.name, f"line {line_number} is not a JSON record")
            field_names.update(record)

        missing, unexpected = compare_field_names(field_names)
        if missing or unexpected:
            raise LayoutMismatchError(path.name, missing, unexpected)
        return LayoutCheck(len(lines), frozenset(field_names))

    def stage_lines(self, cursor: duckdb.DuckDBPyConnection, path: Path, table: str) -> None:
        """Read every line into a temporary table (line_number, line), streamed by DuckDB.

        The delimiter is a control character, which valid JSON never contains unescaped,
        so each line arrives as one value, unchanged.
        """
        try:
            cursor.execute(
                f"""
                CREATE OR REPLACE TEMP TABLE {table} AS
                SELECT row_number() OVER () AS line_number, line
                FROM read_csv(?, columns = {{'line': 'VARCHAR'}}, delim = '\x01', quote = '',
                              escape = '', header = false, auto_detect = false,
                              max_line_size = 1000000000, parallel = false, strict_mode = false)
                """,
                [str(path)],
            )
        except duckdb.Error as error:
            raise UnreadableFileError(path.name, None) from error
