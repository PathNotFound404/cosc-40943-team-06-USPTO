# USPTO Patent Intelligence (Team 06)

A desktop application that imports the USPTO's weekly office action bulk file and stores every record on your own computer, ready for charts. Everything runs locally: no server, no cloud service, no network connection.

Release 1.0 is in progress. What works today is **importing a weekly file** (`UC-FEAT-decompile-files`). Charts, source verification, and export come with later use cases; see [docs/traceability.md](docs/traceability.md) for the status of each.

This README is for running the application from source. The packaged macOS app is not built yet.

## What you need

- **Python 3.14.** On macOS, from [python.org](https://www.python.org/downloads/) or Homebrew (`python3.14 --version` should work). On Windows, from python.org, which installs the `py` launcher (`py -3.14 --version` should work).
- **Git**, to clone the repository.
- **A weekly office action file** to import, one JSON record per line, from the USPTO Open Data Portal. The team's sample is `example data/bdr_oa_bulkdata_weekly_2026-10-18.json`. It isn't in the repository (the folder is git-ignored), so ask the team for a copy and put it in an `example data` folder at the repository root.

## Set up (once)

From the repository root:

**macOS**

```sh
python3.14 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

**Windows (PowerShell)**

```powershell
py -3.14 -m venv .venv
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

`requirements.txt` pins every package: DuckDB, PySide6, pytest, and ruff.

## Run the application

In every new terminal, activate the virtual environment, set the two environment variables, and start the app.

**macOS**

```sh
source .venv/bin/activate
export PATENT_INTELLIGENCE_DATA=./data
export PYTHONPATH=src
python -m patent_intelligence.app
```

**Windows (PowerShell)**

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
.\.venv\Scripts\Activate.ps1
$env:PATENT_INTELLIGENCE_DATA = ".\data"
$env:PYTHONPATH = "src"
python -m patent_intelligence.app
```

- `PATENT_INTELLIGENCE_DATA` is the folder for the database and the log file. `./data` is git-ignored. Without it, the app uses the production folder, `~/Library/Application Support/USPTO Patent Intelligence` (architecture 8.2.6).
- `PYTHONPATH=src` lets Python find the code in `src/patent_intelligence/`.

## Import a weekly file

1. The window opens on the **Import** tab.
2. Drag one or more weekly files from Finder or File Explorer onto the window.
3. A progress bar shows each file's progress. The sample file (383 MB, 8,667 office actions) takes about 20 seconds.
4. A notice appears for each file:
   - **Imported:** the number of records loaded and rejected, with the reason for each rejected record.
   - **Duplicate records:** records whose `id` was already stored are counted too. Every copy is kept, and charts will use the newest.
   - **Already imported:** the same file again changes nothing.
   - **Refused:** a file that isn't a weekly file, has changed fields, or is damaged or only partly downloaded. Nothing from it is stored, and the other files still import.

Quitting during an import is safe: that file's records are discarded, and you can import it again.

## Look at the stored data

Close the app first: while it's running, it holds the database file open. Then, with the virtual environment active:

```sh
python
```

```python
import duckdb
db = duckdb.connect("data/patent-intelligence.duckdb", read_only=True)

db.sql("SELECT * FROM import_log").show()                     # one row per imported file
db.sql("""
    SELECT line_number, id, patentApplicationNumber, groupArtUnitNumber,
           documentCode, submissionDate
    FROM raw_office_action ORDER BY line_number LIMIT 10
""").show()                                                    # the stored records
db.sql("SELECT line_number, reason FROM rejected_record").show() # rejected records and why
db.sql("SHOW TABLES").show()
```

What you'll see:
- **Text values:** every field is stored as the text the file gave, so an art unit shows as `'1234'`.
- **Empty values:** NULL means the field wasn't in that record.
- **Letter text:** `oaText` holds the full office action letter, so leave it out of wide queries.

The log file is `data/logs/patent-intelligence.log`. It holds counts and outcomes only, never letter text, records, or examiner numbers.

To start over with an empty database, close the app and delete the `data` folder.

## Develop and test

With the virtual environment active, from the repository root:

```sh
pytest                               # every test; a few seconds
pytest tests/ingestion -q            # one component's tests
ruff format . && ruff check .        # format and lint (CI runs both)
```

On Windows PowerShell 5.1, run the last line as `ruff format . ; ruff check .`.

The tests use small fixture files in `tests/fixtures/` and never the full sample file. The UI tests run Qt offscreen, so they need no display.

### Where things are

| What | Where |
|---|---|
| Application code, one package per component | `src/patent_intelligence/` (`ingestion`, `storage`, `jobs`, `ui`) |
| Database schema | `src/patent_intelligence/storage/migrations/` (applied on start-up) |
| Tests and fixtures | `tests/` |
| Requirements, use cases, business rules | `docs/requirements/` |
| Architecture and designs | `docs/design/` |
| Team rules and the agent charter | `docs/team-contract.md`, `CLAUDE.md` |

## Troubleshooting

- **"running scripts is disabled on this system" (Windows):** run the `Set-ExecutionPolicy -Scope Process ...` line before activating. It applies only to the current terminal.
- **`ModuleNotFoundError: No module named 'patent_intelligence'`:** `PYTHONPATH` isn't set in this terminal. Set it as shown above.
- **`ModuleNotFoundError: No module named 'duckdb'` (or `PySide6`):** the virtual environment isn't active, or `pip install -r requirements.txt` hasn't been run.
- **"Could not set lock on file" when opening the database:** the app is still running. Close it first.
- **The app says the data folder could not be opened:** check that `PATENT_INTELLIGENCE_DATA` points to a folder you can write to.
- **`UnicodeEncodeError` from `.show()` (Windows):** the terminal isn't using UTF-8. Run `$env:PYTHONIOENCODING = "utf-8"` before starting `python`.
