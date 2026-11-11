# USPTO Patent Intelligence

A desktop application for macOS and Windows that turns the USPTO's weekly office action bulk file into charts about USPTO examination activity. Import a Weekly Release, create visualizations, open the source records behind any figure, and export labeled images ready to post.

Everything runs on your own computer. The application makes no network connections and uses no cloud or AI service, so it works with Wi-Fi turned off.

**Current release:** 1.1.0, for Macs with Apple silicon (M1 or later) running macOS 15 Sequoia or later, and for 64-bit Windows 10 or 11.

## What it does

| Feature | Use case |
|---|---|
| **Import** weekly office action files by dragging them onto the window. Bad records are rejected with a reason; damaged, partial, or unrecognized files are refused without storing anything; importing the same file twice changes nothing. | `UC-FEAT-decompile-files` |
| **Build the staged dataset** automatically after each import, ready for charting. | `UC-FEAT-clean-data` |
| **Create visualizations** of examination activity (see below). | `UC-FEAT-create-visuals` |
| **View the source records** behind a visualization, or behind a single bar, with the source file, import date, and the full office action text. | `UC-FEAT-verify-source` |
| **Export** visualizations as labeled PNG images. | `UC-FEAT-export-visuals` |

Release 1.0 includes six visualizations:

- Office actions by Document Code
- Office actions by Technology Center
- Office actions by Art Unit
- Rejections by type
- Rejection types by Technology Center
- Document Codes by Technology Center

See [docs/traceability.md](docs/traceability.md) for the status of every use case.

---

## Install the app (macOS)

You don't need Python or the Terminal to use the app.

1. Download `USPTO-Patent-Intelligence-<version>-arm64.dmg` from the [latest release](https://github.com/PathNotFound404/cosc-40943-team-06-USPTO/releases/latest).
2. Open the `.dmg` and drag **USPTO Patent Intelligence** onto **Applications**.
3. **First launch only:** the app isn't registered with Apple, so macOS blocks it the first time. Open it once, click **Done**, then go to **System Settings → Privacy & Security**, scroll to **Security**, and click **Open Anyway**. After that it opens normally.

## Install the app (Windows)

1. Download `USPTO-Patent-Intelligence-<version>-x64-setup.exe` from the [latest release](https://github.com/PathNotFound404/cosc-40943-team-06-USPTO/releases/latest).
2. Run it. The installer isn't signed, so SmartScreen may say **"Windows protected your PC"**: click **More info → Run anyway**.
3. Follow the installer. It installs for your account only (no administrator password) and adds a Start menu shortcut and an uninstaller.

The [user guide](docs/user-guide.md) covers installation step by step, plus updating, backing up, and removing the app.

### Using the app

The window has four tabs:

- **Import:** drag one or more weekly files from Finder onto the window. A progress bar shows each file, then a notice reports how many records were stored and how many were rejected, and why. The sample file (383 MB, 8,667 office actions) takes about 20 seconds. Quitting during an import is safe: that file's records are discarded, and you can import it again.
- **Visualizations:** choose the imported data and the visualizations you want, then click **Create visualizations**.
- **Sources:** click **View source records** on a chart, or click one of its bars, to see the office actions behind it. Select a record to read its letter text.
- **Export:** choose visualizations, click **Export…**, and pick a folder. Each one is saved as a labeled PNG.

### Where your data is kept

All imported data lives in `~/Library/Application Support/USPTO Patent Intelligence` (macOS) or `%LOCALAPPDATA%\USPTO Patent Intelligence` (Windows), not inside the app, so replacing the app with a new release keeps your data. The folder holds the database (`patent-intelligence.duckdb`) and a log file (`logs/patent-intelligence.log`), which records counts and outcomes only, never office action text or examiner numbers. To back up, quit the app and copy the folder.

---

## Run from source (developers)

### Prerequisites

- **Python 3.14.** On macOS, from [python.org](https://www.python.org/downloads/) or Homebrew (`python3.14 --version`). On Windows, from python.org, which installs the `py` launcher (`py -3.14 --version`).
- **Git.**
- **A weekly office action file** to import (one JSON record per line, from the USPTO Open Data Portal). The team's sample, `bdr_oa_bulkdata_weekly_2026-10-18.json`, isn't in the repository; ask the team for a copy and put it in an `example data/` folder at the repository root, which is git-ignored. Never commit it.

The code runs on both macOS and Windows.

### Set up (once)

```sh
git clone https://github.com/PathNotFound404/cosc-40943-team-06-USPTO.git
cd cosc-40943-team-06-USPTO
```

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

`requirements.txt` pins every runtime and development package (DuckDB, matplotlib, PySide6, pytest, ruff). `requirements-build.txt` adds PyInstaller, which you need only to build the app.

### Run the application

In each new terminal, activate the virtual environment, set two environment variables, and start the app.

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

- `PATENT_INTELLIGENCE_DATA` is the folder for the database and log file. `./data` is git-ignored. Without it, the app uses the production folder above (architecture 8.2.6). To start over with an empty database, close the app and delete `data/`.
- `PYTHONPATH=src` lets Python find the code in `src/patent_intelligence/`.

### Test and lint

With the virtual environment active, from the repository root:

```sh
pytest                               # every test; a few seconds
pytest tests/ingestion -q            # one component's tests
ruff format . && ruff check .        # format and lint (CI runs both)
```

On Windows PowerShell 5.1, use `ruff format . ; ruff check .` instead.

Tests use small fixture files in `tests/fixtures/`, never the full sample file. UI tests run Qt offscreen, so they need no display.

### Build and release

CI builds the app; you don't need to build it yourself to release (architecture section 7, `KD-packaging-pyinstaller`).

- **Every pull request** runs `ruff` and `pytest` on macOS and Windows ([ci.yml](.github/workflows/ci.yml)).
- **Pull requests that change packaging** (`packaging/`, a requirements file, `settings.py`, or the release workflow) also build the DMG and the Windows installer. Download them from the run's artifacts. You can also run Actions → Release → Run workflow on `main`.
- **A release** is a version tag on `main`, such as `v1.0.0`, that matches `__version__` in `src/patent_intelligence/__init__.py`. The tag runs [release.yml](.github/workflows/release.yml) on an Apple silicon runner and a Windows runner. Each builds the app and starts it once as a smoke test; the Mac build is wrapped in a DMG and the Windows build in an Inno Setup installer, and both are published as one GitHub Release using `docs/release-notes/<version>.md`. Bump `__version__` and add the release notes in a pull request before tagging.

To build locally on an Apple silicon Mac:

```sh
pip install -r requirements-build.txt
sh packaging/build_macos.sh             # → dist/USPTO-Patent-Intelligence-<version>-arm64.dmg
```

To build locally on 64-bit Windows, install [Inno Setup 6](https://jrsoftware.org/isinfo.php) first, then:

```powershell
pip install -r requirements-build.txt
.\packaging\build_windows.ps1           # → dist\USPTO-Patent-Intelligence-<version>-x64-setup.exe
```

The Mac app is ad-hoc signed but not notarized, and the Windows installer is unsigned (`OI-12`, `RISK-unsigned-app`). That is why macOS and Windows ask for confirmation the first time.

---

## Project layout

| What | Where |
|---|---|
| Application code, one package per component | `src/patent_intelligence/` (`ingestion`, `cleaning`, `storage`, `analytics`, `charts`, `provenance`, `jobs`, `ui`) |
| Database schema (applied on start-up) | `src/patent_intelligence/storage/migrations/` |
| Tests and fixtures | `tests/` |
| Packaging (PyInstaller spec, macOS and Windows build scripts, Inno Setup script, smoke test) | `packaging/` |
| CI and release workflows | `.github/workflows/` |
| Release notes | `docs/release-notes/` |

## Documentation

| Document | What it covers |
|---|---|
| [User guide](docs/user-guide.md) | Installing, using, updating, and removing the app |
| [Vision and scope](docs/requirements/vision-and-scope.md) | Why the project exists and what release 1.0 includes |
| [Use cases](docs/requirements/use-cases.md) | What the application does, step by step |
| [Business rules](docs/requirements/business-rules.md) | Acceptance criteria |
| [Software requirements specification](docs/requirements/software-requirements-specification.md) | Quality attributes, functional requirements, constraints |
| [Glossary](docs/requirements/project-glossary.md) | Project vocabulary |
| [Open issues](docs/requirements/OPEN-ISSUES.md) | Unanswered questions |
| [Architecture](docs/design/architectural-design.md) | Components, key decisions, and binding conventions (section 8) |
| [Traceability](docs/traceability.md) | Status of every use case |
| [Team contract](docs/team-contract.md) | Reviews, branches, and decisions |
| [CLAUDE.md](CLAUDE.md) | Charter for AI coding agents |

## Contributing

One use case becomes one issue, one branch, one pull request, and one set of tests. Work on a branch, never on `main`; pull requests need the approvals in [team-contract.md](docs/team-contract.md) section 5, and update the use case's row in [traceability.md](docs/traceability.md). Fill in the [pull request template](.github/PULL_REQUEST_TEMPLATE.md).

## Troubleshooting

- **macOS says the app "cannot be verified" or "Not Opened":** this is expected on first launch. Use **Open Anyway** in System Settings → Privacy & Security (see [Install the app](#install-the-app-macos)).
- **Windows says "Windows protected your PC" when running the installer:** expected, because the installer is unsigned. Click **More info → Run anyway**.
- **"running scripts is disabled on this system" (Windows):** run the `Set-ExecutionPolicy -Scope Process ...` line before activating. It applies only to the current terminal.
- **`ModuleNotFoundError: No module named 'patent_intelligence'`:** `PYTHONPATH` isn't set in this terminal.
- **`ModuleNotFoundError: No module named 'duckdb'` (or `PySide6`):** the virtual environment isn't active, or `pip install -r requirements.txt` hasn't been run.
- **"The data folder … could not be written to":** check that `PATENT_INTELLIGENCE_DATA` (from source) points to a folder you can write to, or that the disk isn't full.
- **Anything else:** the app shows a message and writes details to `logs/patent-intelligence.log` in the data folder. Send that file to the team.
