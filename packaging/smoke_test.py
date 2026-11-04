"""Start the built app once and check that it opened its database.

Usage: python packaging/smoke_test.py <path to the built executable>

The app runs offscreen with a temporary data folder (architecture 8.2.6) until its log
shows the schema migrations were applied, then it is stopped. This catches files and
modules PyInstaller left out, which the source tests cannot see. A missing migrations
folder would leave an empty database without any error, so the tables are checked too.
"""

import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import duckdb

LOG_LINE = "Applied schema migration 001_raw_tables.sql"
TIMEOUT_SECONDS = 60


def main(executable: Path) -> int:
    with tempfile.TemporaryDirectory() as folder:
        data_folder = Path(folder)
        log_path = data_folder / "logs" / "patent-intelligence.log"
        environment = os.environ | {
            "PATENT_INTELLIGENCE_DATA": str(data_folder),
            "QT_QPA_PLATFORM": "offscreen",
        }
        process = subprocess.Popen([str(executable)], env=environment)
        try:
            started = _wait_for_log(process, log_path)
        finally:
            process.kill()
            process.wait()
        if not started:
            print(f"FAIL: the app did not log '{LOG_LINE}' within {TIMEOUT_SECONDS} s.")
            if log_path.exists():
                print(log_path.read_text(encoding="utf-8"))
            return 1

        connection = duckdb.connect(str(data_folder / "patent-intelligence.duckdb"))
        tables = {row[0] for row in connection.execute("SHOW TABLES").fetchall()}
        connection.close()
        for table in ("schema_migration", "import_log", "raw_office_action"):
            if table not in tables:
                print(f"FAIL: the database has no {table} table. Tables: {sorted(tables)}")
                return 1
    print("OK: the built app started, opened its database, and applied its migrations.")
    return 0


def _wait_for_log(process: subprocess.Popen, log_path: Path) -> bool:
    deadline = time.monotonic() + TIMEOUT_SECONDS
    while time.monotonic() < deadline:
        if log_path.exists() and LOG_LINE in log_path.read_text(encoding="utf-8"):
            return True
        if process.poll() is not None:
            print(f"FAIL: the app exited with code {process.returncode} during start-up.")
            return False
        time.sleep(0.5)
    return False


if __name__ == "__main__":
    sys.exit(main(Path(sys.argv[1])))
