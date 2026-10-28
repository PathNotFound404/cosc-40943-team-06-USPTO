# CLAUDE.md: USPTO Patent Intelligence (Team 06)

This is the team's charter for AI agents. Every agent session reads it. It points to where decisions live rather than repeating them; when this file and a document disagree, the document wins and this file should be fixed.

## What we are building

A single-user macOS desktop application for Malachi Hernandez. It imports the USPTO's weekly office action bulk file, turns it into charts about USPTO examination activity, lets him open the records behind any figure, and exports labeled images for his posts. Everything runs on his computer, with no cloud services and no AI in release 1.0.

## Where things are

| What | Where |
|---|---|
| Why we are building it, scope, MVP | [docs/requirements/vision-and-scope.md](docs/requirements/vision-and-scope.md) (section 4.3 is the MVP) |
| What to build (the contract) | [docs/requirements/use-cases.md](docs/requirements/use-cases.md) |
| Business rules (acceptance criteria) | [docs/requirements/business-rules.md](docs/requirements/business-rules.md) |
| Quality attributes, `FR-*`, constraints, data | [docs/requirements/software-requirements-specification.md](docs/requirements/software-requirements-specification.md) |
| Vocabulary | [docs/requirements/project-glossary.md](docs/requirements/project-glossary.md) |
| Unanswered questions | [docs/requirements/OPEN-ISSUES.md](docs/requirements/OPEN-ISSUES.md) |
| Architecture and binding conventions | [docs/design/architectural-design.md](docs/design/architectural-design.md) (section 8 is binding on all code) |
| Design-of-record template | [docs/design/design-of-record.md](docs/design/design-of-record.md); designs go in `docs/design/<area>.md` |
| Status of every use case | [docs/traceability.md](docs/traceability.md) |
| Team rules (reviews, branches, decisions) | [docs/team-contract.md](docs/team-contract.md) |
| Pull request description | [.github/PULL_REQUEST_TEMPLATE.md](.github/PULL_REQUEST_TEMPLATE.md) |

## How work is done

- One use case becomes one issue, one branch, one pull request, and one set of tests.
- Build in two stages: `/design <UC-ID>` writes the design-of-record and stops before code; `/implement <UC-ID>` builds only from a merged design, in a fresh session.
- Work on a branch, never on `main`. A pull request needs the approvals in [team-contract.md](docs/team-contract.md) section 5, from teammates who do not own the use case.
- Update the use case's row in [traceability.md](docs/traceability.md) section 3 in the same pull request.
- The proving slice is `UC-FEAT-decompile-files` (architecture section 6).

## Stack

These were decided in [architecture section 9.2](docs/design/architectural-design.md#92-key-decisions). Do not substitute alternatives.

- Python 3.12, with `pip` and a virtual environment (`requirements.txt`)
- PySide6 for the user interface; matplotlib for charts (`KD-ui-framework`)
- DuckDB as one local database file, opened in-process, with a pinned version (`KD-embedded-duckdb`)
- `pytest` for tests; `ruff` for linting and formatting
- PyInstaller for the macOS app; GitHub Actions for CI (`KD-packaging-pyinstaller`)
- Target: macOS on Apple silicon. Developers use both macOS and Windows, so code must run on both.

## Commands

There is no code yet. The first slice creates `requirements.txt` and the package layout; update this section when it does.

```sh
python3.12 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
ruff format . && ruff check .
pytest
```

## Conventions

The rules are in [architecture section 8.2](docs/design/architectural-design.md#82-other-concepts). Follow them, cite them, and do not restate them in code comments or designs:

- **Errors (8.2.1):** the application's own exceptions are caught once per action in the UI. A bad record is a rejected record with a reason, not an exception.
- **Time (8.2.2):** store UTC as supplied; display YYYY-MM-DD; pass the import time in as a parameter.
- **Components (8.2.3):** only Storage opens DuckDB connections; the UI calls each component's public functions.
- **Code (8.2.4):** one package per component; glossary terms for names; bulk work in DuckDB SQL, not pandas.
- **Validation (8.2.5):** the check that counts is in Ingestion, before anything is stored.
- **Configuration (8.2.6):** only the data folder differs between development and production.
- **Logging (8.2.7):** never log office action text, whole records, or examiner numbers.
- **Persistence (8.2.8):** one transaction per imported file; raw tables are append-only.
- **Auditing (8.2.9):** every raw record carries its import ID.
- **Testing (8.2.10):** small fixture files under the tests folder. Never use the full sample file in tests.

## Vocabulary

Use the [glossary](docs/requirements/project-glossary.md) terms exactly, in code, UI text, and documents, including Office Action, Art Unit, Technology Center, Work Group, Examiner, Rejection, Document Code, Application Number, and Weekly Release. Architecture terms are in [architecture section 12](docs/design/architectural-design.md#12-glossary): Import, Raw records, Staged dataset, Metric, and Provenance. Do not introduce synonyms.

## Rules for the agent

**Never:**

- Add a dependency until a person confirms it exists and is the package we meant.
- Remove the `Co-Authored-By` trailer from a commit.
- Commit or push to `main`, or merge a pull request.
- Rename, renumber, or repoint an identifier (`UC-*`, `BR-*`, `FR-*`, `KD-*`, `OI-*`, and the rest). Cite identifiers; do not restate what they say.
- Invent a business rule, a threshold, a field meaning, or a client preference. Ask, and add the question to `OPEN-ISSUES.md`.
- Make network calls or import a network library, send telemetry, or use any cloud or AI service (`SEC-no-data-egress`, `CO-local-execution`, `KD-no-ai-in-mvp`).
- Change, fill in, or guess a raw record value (`BR-no-data-alteration`).
- Commit anything from `example data/`.
- Add anything the use case does not ask for: no admin overrides, retry queues, status fields, or extra notifications.

**Always:**

- Challenge the specification when it is ambiguous, contradictory, or out of date. Name the gap and propose the fix; do not silently comply or fill it in.
- Write a test for the main success scenario and every extension of the use case you build.
- Report test results faithfully, including what was skipped.

## Data

The sample weekly file is `example data/bdr_oa_bulkdata_weekly_2026-10-18.json`: 8,667 office actions, 383 MB, one JSON record per line. The folder is git-ignored. Use it only for manual checks, and cut small fixtures from it for tests.
