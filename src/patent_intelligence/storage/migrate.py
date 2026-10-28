"""Numbered schema migrations, applied in order on start-up (architecture 8.2.8)."""

import logging
from pathlib import Path

import duckdb

MIGRATIONS_FOLDER = Path(__file__).parent / "migrations"

log = logging.getLogger(__name__)


def apply_migrations(
    connection: duckdb.DuckDBPyConnection, folder: Path = MIGRATIONS_FOLDER
) -> list[int]:
    """Apply every `NNN_name.sql` script not yet applied, each in its own transaction.

    Returns the versions applied by this call.
    """
    connection.execute(
        "CREATE TABLE IF NOT EXISTS schema_migration "
        "(version INTEGER PRIMARY KEY, script TEXT NOT NULL)"
    )
    applied = {
        row[0] for row in connection.execute("SELECT version FROM schema_migration").fetchall()
    }
    newly_applied = []
    for script in sorted(folder.glob("[0-9][0-9][0-9]_*.sql")):
        version = int(script.name[:3])
        if version in applied:
            continue
        connection.begin()
        try:
            connection.execute(script.read_text(encoding="utf-8"))
            connection.execute(
                "INSERT INTO schema_migration (version, script) VALUES (?, ?)",
                [version, script.name],
            )
        except BaseException:
            connection.rollback()
            raise
        connection.commit()
        log.info("Applied schema migration %s", script.name)
        newly_applied.append(version)
    return newly_applied
