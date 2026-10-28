# Use Cases

**Project:** USPTO Patent Intelligence
**Team:** Group 6, Bradley, Koen, Cody, Edwin, Tanner, Turner
**Client:** Malachi
**Version:** 1.2

---

_**How to use this template.** Instructions appear in italic square brackets. Fill in underneath them and leave them in place until the document is stable._

_**What a use case is.** One goal a user can accomplish with your system, written as the dialogue between the actor and the system, including what happens when it goes wrong. It is the unit of work in this course: one use case becomes one issue, one branch, one pull request, and one set of tests._

_**Why the use case and not the user story.** You will meet user stories in industry, and they are a good planning tool: "As a student, I want to submit my report so that I get credit." A story is deliberately under-specified, because it is a **placeholder for a conversation** that happens later, between people. That is exactly the wrong property when the thing building your code is an agent that will implement precisely what the specification says and never ask what you meant. Use stories to plan and prioritize. Build against use cases._

_The difference that matters is the parts a story does not have: preconditions, the step-by-step flow, and above all the **extensions**, which is where the failure paths live. Most defects your team ships this semester will be in a path nobody wrote down._

## Identifiers

_Use cases are identified as `UC-<AREA>-<slug>`, where the area code groups related functionality and the slug is coined from the goal: `UC-RUB-create-rubric`, `UC-WAR-manage-activities`, `UC-STU-invite-students`._

_Pick your own area codes from your project's feature areas, three or four letters each, and list them at the top of the Use Case List. Areas correspond to the `FEAT-*` entries in your [vision and scope](vision-and-scope.md), which is where use cases come from._

_**Never renumber, rename, or repoint an identifier.** Moving a use case between areas would change its identifier, so put it in the right area the first time, and if you get it wrong, leave it. An identifier is an address, not a description._

_Within one use case, `PRE-1`, `POST-1`, and the step numbers are local and may be renumbered freely, because nothing outside the use case cites them._

## Revision History

| Date | Version | Description | Author |
|---|---|---|---|
| Not recorded | 0.1 | Initial use cases derived from the vision and scope feature list | Not recorded |
| 2026-09-25 | 1.0 | Create major use cases week 5. The first 4 most substantial use cases defined. | Tanner, Bradley |
| 2026-10-26 | 1.1 | Filled introduction and use case list; removed worked example; added `UC-FEAT-verify-source` and `UC-FEAT-export-visuals`; completed Associated Information and fixed extension numbering | Tanner |
| 2026-10-28 | 1.2 | Marked `UC-FEAT-query-ai` deferred and linked it to `FEAT-Query-AI`; added business rules to `UC-FEAT-create-visuals`; linked open issues; fixed glossary references and bracketed dates | Cody Pinkston |

---

## 1. Introduction

### 1.1 Purpose

_[One paragraph: this document specifies the goals users can accomplish with the system, in enough detail that a developer knows what to build and a tester knows what to check.]_

This document specifies the goals the client can accomplish with USPTO Patent Intelligence: importing weekly USPTO office action bulk data, cleaning it, turning it into visualizations, tracing any visualization back to its source data, and exporting visualizations for posts. It also specifies asking a local AI questions answered only from the processed data, which is deferred to a later release. Each use case is written in enough detail that a developer knows what to build and a tester knows what to check.

### 1.2 Scope

_[Which feature areas from the vision and scope are covered here. Name the `FEAT-*` entries. If a feature has no use cases yet, say so rather than leaving the reader to notice.]_

This document covers the three MVP features in [vision-and-scope.md](vision-and-scope.md) section 4.3:

- `FEAT-Intake-Data`: `UC-FEAT-decompile-files`, `UC-FEAT-clean-data`.
- `FEAT-Generate-Visualization`: `UC-FEAT-create-visuals`, `UC-FEAT-export-visuals`.
- `FEAT-Verify-Source`: `UC-FEAT-verify-source`.

`FEAT-Query-AI` (a stretch feature in vision and scope 4.3): `UC-FEAT-query-ai`. It is **deferred**: release 1.0 has no AI features (architecture `KD-no-ai-in-mvp`), so it is specified but not built.

The out-of-scope features `FEAT-Link-Datasets`, `FEAT-Detect-Anomalies`, `FEAT-Historical-Overview`, and `FEAT-International-Data` have no use cases yet.

---

## 2. Use Case Template

_[The field definitions. Every use case below uses exactly these fields, in this order.]_

**UC ID and Name.** _The identifier plus a concise name stating the value this use case provides to a user. Begin with an action verb, followed by an object: "Create a rubric", not "Rubric creation" and not "Rubric management", which is a feature, not a goal._

**Created By** and **Date Created.** _Who wrote it, and when._

**Primary and Secondary Actors.** _An actor is a person or other entity outside the system that interacts with it. The primary actor initiates this use case; secondary actors participate in completing it. Actors usually correspond to the user classes you identified in the vision and scope._

**Trigger.** _The business event, system event, or user action that starts the use case. The trigger tells the system to begin testing the preconditions._

**Description.** _A brief statement of the reason for and the outcome of this use case._

**Preconditions.** _What must already be true before this use case can start. **The system must be able to test each precondition**, which is what separates a precondition from a hope. Label them `PRE-1`, `PRE-2`. Example: PRE-1. The user's identity has been authenticated._

**Postconditions.** _The state of the system at successful conclusion. Label them `POST-1`, `POST-2`. Example: POST-1. The price of the item in the database has been updated with the new value._

**Main Success Scenario.** _The actor's actions and the system's responses under normal, expected conditions, as a numbered list that alternates between the two and ends by accomplishing the goal in the name. Write "The system validates..." not "The system will validate..."; use cases are written in the present tense._

**Extensions.** _Where the real work is. Two kinds, both numbered relative to the step they branch from:_

- _**Alternative flows**, other ways the use case can still succeed. Number them `4a`, `4b` for branches from step 4, with their own sub-steps `4a1`, `4a2`. Say where the flow branches off and, if it does, where it rejoins._
- _**Exceptions**, anticipated error conditions and how the system responds. Numbered the same way._

_**A use case with no extensions is not finished.** For every step, ask: what if the input is invalid, the thing is not found, the user cancels, the user is not allowed, or the external system is down? An agent building from a flow with no failure paths will invent the error handling, and you will not find out until a demo._

**Priority.** _Relative priority of implementing this. Use the same scheme across all your use cases._

**Frequency of Use.** _Roughly how often this is performed, per an appropriate unit of time. An early indicator of load, concurrency, and transaction volume, and it is the field that tells your architecture which use cases matter._

**Business Rules.** _The `BR-*` identifiers that govern this use case. **Identifiers only, never the rule's text**, so the rule has one home in [business-rules.md](business-rules.md) and cannot go stale here._

**Associated Information.** _Everything a developer needs that is not a step: the data fields and their validation rules, quality attributes that apply, display and sort strategies, and what happens if execution fails for a systemic reason such as a network timeout. If the use case makes a durable change, say whether a failure rolls it back, completes it, or leaves it partially done._

_Data fields are specified as a table:_

| Property name | Data type | Validation rule | Security or access concerns | Glossary reference |
|---|---|---|---|---|
| _[field]_ | _[type]_ | _[required, format, range]_ | _[who may see or set it]_ | _[term]_ |

**Related Use Cases.** _Other use cases this one invokes or is invoked by, by identifier and name._

**Assumptions.** _Anything assumed about this use case or how it executes._

**Open Issues.** _What you do not know yet. Mirror it into [OPEN-ISSUES.md](OPEN-ISSUES.md) so it is visible in one place._

---

## 3. Use Case List

_[Your area codes, then a table of every use case by area. Write this list first, before specifying any single use case in detail. It is the cheapest thing to review with your client, and finding out you missed a whole area costs minutes here rather than a week later.]_

| Area code | Feature area | Use cases |
|---|---|---|
| FEAT | Data intake, from `FEAT-Intake-Data` | `UC-FEAT-decompile-files`, `UC-FEAT-clean-data` |
| FEAT | Visualization, from `FEAT-Generate-Visualization` | `UC-FEAT-create-visuals`, `UC-FEAT-export-visuals` |
| FEAT | Source verification, from `FEAT-Verify-Source` | `UC-FEAT-verify-source` |
| FEAT | Local AI assistant, from `FEAT-Query-AI` (deferred) | `UC-FEAT-query-ai` |

All current use cases share the area code `FEAT`. The identifiers were already in use, and identifiers are never renamed.

---

## 4. Use Cases

_[One `###` heading per use case, grouped under a `##` heading per area. Worked example below, taken from Project Pulse. Delete it and write your own.]_

### UC-FEAT-decompile-files: Selected bulk files from USPTO office action data is decompiled

**UC ID and Name:** UC-FEAT-decompile-files: Decompile files

**Created By:** Bradley Helmholz

**Date Created:** 2026-09-22

**Primary actor:** User

**Secondary Actors:** None

**Trigger:** User inputs file to decompile

**Description:** The user inputs their bulk data file that has been chosen into the system, and it is decompiled for later use

**Preconditions:**
- PRE-1. User has bulk USPTO office action data file available for selection

**Postconditions:**
- POST-1. Bulk file is decompiled into multiple usable files of data

**Main Success Scenario:**
1. User selects bulk data file
2. Indicates to decompile
3. System validates selected file is supported bulk data format
4. System extracts individual records contained within
5. System converts each record into usable file of data
6. System stores decompiled files in quick database for later use
7. System confirms to user that decompiling is complete
8. Use case ends

**Extensions:**
- 3a. Selected file is not supported bulk data format:
    - 3a1. System alerts user that file format is invalid
    - 3a2. User selects different file, or terminates use case
- 4a. Bulk file is corrupted or unreadable
    - 4a1. System alerts user that file could not be read
    - 4a2. User selects different file, or terminates use case
- 5a. One or more records fail to convert to usable format
    - 5a1. System logs failed records count and continues processing remainder
    - 5a2. System notifies user of number of records that failed to convert

**Priority: High**

**Frequency of Use:** Occasional; used primarily once a week in the long run when new USPTO office action data acquired

**Business Rules:**
- `BR-weekly-uspto-publication`
- `BR-weekly-office-action-data`
- `BR-art-unit-assignment`
- `BR-office-action-issued`

**Associated Information:**

| Property name | Data type | Validation rule | Security or access concerns | Glossary reference |
|---|---|---|---|---|
| bulk data file | File | Required; must be a supported USPTO office action bulk format | none; local desktop app, single user | Office Action, Weekly Release |

Failure handling: decompiling writes to storage only after records are extracted. If execution fails part way, records already stored remain, and the source file and record count are kept with them (`DI-source-tracking`). Re-importing the same file does not create duplicates (`DI-no-duplicates`).

Quality attributes: processing does not need to be fast and may run unattended (`AS-speed-not-critical`). Weekly files can be up to 20-50 GB.

**Related Use Cases:** `UC-FEAT-clean-data`: Clean decompiled data.

**Assumptions:** none

**Open Issues:**

- Which exact bulk file formats are supported (ZIP containing XML, JSON, or other). One JSON-lines sample has been received; more are requested (`OI-6`, `OI-14`, `DE-client-sample-data`).

---

### UC-FEAT-query-ai: Ask local AI a question about processed data

> **Deferred:** not built in release 1.0. The MVP has no AI features ([architecture-of-record](../design/architectural-design.md) `KD-no-ai-in-mvp`; `FEAT-Query-AI` is a stretch feature in vision and scope 4.3).

**UC ID and Name:** UC-FEAT-query-ai: Ask AI assistant

**Created By:** Bradley Helmholz

**Date Created:** 2026-09-22

**Primary actor:** User

**Secondary Actors:** None

**Trigger:** User submits natural language query about processed data

**Description:** The user inputs their question in natural language and local AI model answers strictly from processed dataset without unknown extrapolation, citing underlying data used without fabrication

**Preconditions:**
- PRE-1. Data has been processed and is available for query
- PRE-2. Local AI model is loaded and running

**Postconditions:**
- POST-1. Answer based on existing given processed data is returned to the user, along with citations

**Main Success Scenario:**
1. User moves to AI assistant window
2. User submits natural language question
3. System retrieves relevant records currently loaded that match the question
4. System passes retrieved records to local AI model and grounding context
5. System generates answer using only retrieved records
6. System confirms that local AI model has information grounded in real context
7. System displays answer along with citations to the source records used
8. Use case ends

**Extensions:**
- 2a. AI model cannot understand the query user submitted
    - 2a1. System informs user it cannot understand the query that has been submitted and use case ends
- 3a. No relevant records found
    - 3a1. System informs user no data supports answer to given question and use case ends
- 4a. AI model cannot produce answer strictly grounded in retrieved records
    - 4a1. System informs user no verifiable answer can be generated based on the records alone, instead of returning unsupported answer, and use case ends

**Priority:** High
**Frequency of Use:** Frequent; user may query many times on given datasets about many topics and analysis points

**Business Rules:**
- `BR-office-action-issued`
- `BR-102-rejection`
- `BR-103-rejection`
- `BR-112-rejection`
- `BR-double-patenting`
- `BR-weekly-uspto-publication`
- `BR-weekly-office-action-data`
- `BR-separate-dataset-domains`
- `BR-cross-record-linkage`
- `BR-patent-lineage`
- `BR-evidence-based-analysis`
- `BR-data-driven-insights`
- `BR-rejection-distribution-metric`
- `BR-pendency-trend-metric`

**Associated Information:**

| Property name | Data type | Validation rule | Security or access concerns | Glossary reference |
|---|---|---|---|---|
| question | String | Required; natural language | none; runs locally, never sent off the computer (`CO-local-execution`) | none |

Display strategy: the answer text, followed by a list of citations; each citation identifies the source record and its source file.

Failure handling: querying does not change stored data. If the local model fails or times out, the system shows an error and no answer.

**Related Use Cases:** `UC-FEAT-decompile-files`: Decompile files; `UC-FEAT-clean-data`: Clean decompiled data; `UC-FEAT-verify-source`: Verify the source of a visualization.

**Assumptions:** AI model is running. Ability to interface with data

**Open Issues:**

- Which local AI runtime and model to use, and their licenses (`CO-open-weight-models`, `CO-model-licensing`); not logged in OPEN-ISSUES until AI comes into scope.

---

### UC-FEAT-create-visuals: The user creates visualizations from imported data

**UC ID and Name:** `UC-FEAT-create-visuals`: Create visualizations from imported data
**Created By:** Tanner Temple
**Date Created:** 2026-09-25
**Primary Actor:** User
**Secondary Actors:** none
**Trigger:** The user indicates to create visualizations after importing data.
**Description:** After the user imports data and it has been decompiled, cleaned, and staged, the user creates visualizations from it in the desktop app. The system runs scripts that produce a visualization tab for each metric, each backed by and linked to the stored data.

**Preconditions:**

- PRE-1. The desktop app is running.
- PRE-2. The imported data has been decompiled and cleaned and is staged for visualization.

**Postconditions:**

- POST-1. Visualizations are displayed on separate tabs, one per metric.
- POST-2. Each visualization links to the stored data behind it, and the user can drill down to view that data.
- POST-3. The visualizations are staged for export.

**Main Success Scenario:**

1. The user indicates to create visualizations.
2. The system confirms the data is cleaned and staged.
3. The system asks the user to choose specific visualization types or all available visualizations.
4. The user selects one or more visualization types, or all, and confirms.
5. The system runs the visualization scripts against the staged data.
6. The system displays each visualization on its own tab, linked to its underlying data.
7. The system stages the visualizations for export.
8. Use case ends.

**Extensions:**

- **2a. Data is not clean (for example, null values or missing columns):**
    - 2a1. The system alerts the user that visualizations cannot be created until the data is cleaned.
    - 2a2. The user either chooses `UC-FEAT-clean-data`: Clean decompiled data, or terminates the use case.
- **4a. The user cancels the selection:**
    - 4a1. The system creates no visualizations and the use case ends.
- **5a. One or more visualization scripts fail:**
    - 5a1. The system logs the failed visualizations and continues creating the rest.
    - 5a2. The system notifies the user which visualizations could not be created.
    - 5a3. The flow rejoins at step 6.
- **6a. The user drills down into a visualization:**
    - 6a1. The user selects a visualization or data point.
    - 6a2. The system displays the underlying stored records.
    - 6a3. The flow returns to step 6.

**Priority:** Very High
**Frequency of Use:** Most frequent. Along with decompressing and cleaning data, this is the most important feature.
**Business Rules:** `BR-evidence-based-analysis`, `BR-data-driven-insights`, `BR-rejection-distribution-metric`, `BR-pendency-trend-metric`

**Associated Information:**

| Property name | Data type | Validation rule | Security or access concerns | Glossary reference |
|---|---|---|---|---|
| visualization type | Enumeration | Optional; one or more of the available types; defaults to all | none; local desktop app | Visualization |

Display strategy: one tab per metric, each with a link to its underlying data.

Failure handling: creating visualizations does not change stored data. If execution fails, the staged data is left unchanged and only the visualizations that completed are shown.

**Related Use Cases:** `UC-FEAT-decompile-files`: Decompile files; `UC-FEAT-clean-data`: Clean decompiled data.
**Assumptions:** The client (Malachi) wants visualizations built only from clean data.
**Open Issues:**

- Which metrics and visualization types are required (`OI-1`).
- Which export format(s) the staged visualizations should support (`OI-2`).
- Whether the user chooses visualization types or always receives all of them (`OI-3`).
- Which field rejection charts count by default, the tag or the letter text (`OI-7`), and how pendency is calculated (`OI-8`).

---

### UC-FEAT-clean-data: The system cleans decompiled data for visualization

**UC ID and Name:** `UC-FEAT-clean-data`: Clean decompiled data
**Created By:** Tanner Temple
**Date Created:** 2026-09-25
**Primary Actor:** User
**Secondary Actors:** none
**Trigger:** The system finishes decompiling the data (`UC-FEAT-decompile-files`).
**Description:** After the user's bulk data file is decompiled, the system cleans it with a script so it is staged for creating visualizations. Cleaning only standardizes and formats; it never adds to or alters the underlying record values.

**Preconditions:**

- PRE-1. The USPTO office action data has been decompiled and stored.

**Postconditions:**

- POST-1. The data is cleaned and staged for visualization.
- POST-2. The original decompiled data values are unchanged apart from the defined cleaning operations.

**Main Success Scenario:**

1. The system confirms the decompiled data is present.
2. The system runs the cleaning script: it standardizes column names, removes null values, and formats fields for visualization, without adding or altering record values.
3. The system validates that the cleaned data contains the columns required for visualization.
4. The system stages the cleaned data and notifies the user that it is ready for visualizations.
5. Use case ends.

**Extensions:**

- **1a. Decompiled data is missing or empty:**
    - 1a1. The system alerts the user that there is no data to clean.
    - 1a2. The user either chooses `UC-FEAT-decompile-files`: Decompile files, or terminates the use case.
- **2a. The cleaning script fails:**
    - 2a1. The system discards the partial result, keeping the decompiled data unchanged.
    - 2a2. The system alerts the user that cleaning failed, and the use case ends.
- **3a. Required columns are missing after cleaning:**
    - 3a1. The system alerts the user and lists the missing columns.
    - 3a2. The system does not stage the data, and the use case ends.

**Priority:** High
**Frequency of Use:** Frequent; every time data is uploaded.
**Business Rules:** `BR-no-data-alteration`

**Associated Information:**

Cleaning operations: standardize column names, remove null values, format fields for visualization. No other changes are permitted.

Failure handling: cleaning runs on a working copy. If execution fails, the change is rolled back and the decompiled data is left as it was.

**Related Use Cases:** `UC-FEAT-decompile-files`: Decompile files; `UC-FEAT-create-visuals`: Create visualizations from imported data.
**Assumptions:** Cleaning runs automatically once decompiling completes; the user does not start it manually.
**Open Issues:**

- The column naming convention to standardize to (`OI-4`).
- Whether null handling removes whole records or only null values, and whether the user sees a count of what was removed (`OI-5`).

---

### UC-FEAT-verify-source: The user verifies the source data behind a visualization

**UC ID and Name:** `UC-FEAT-verify-source`: Verify the source of a visualization
**Created By:** Tanner Temple
**Date Created:** 2026-10-26
**Primary Actor:** User
**Secondary Actors:** none
**Trigger:** The user indicates to view the source of a visualization or data point.
**Description:** The user wants to confirm where a visualization's numbers come from before using it in a post. The system shows the stored records behind the visualization and the USPTO file each record was imported from, giving the paper trail the client requires.

**Preconditions:**

- PRE-1. The desktop app is running.
- PRE-2. At least one visualization has been created (`UC-FEAT-create-visuals`).

**Postconditions:**

- POST-1. The records behind the selected visualization or data point are displayed, each with its source file and import date.
- POST-2. No stored data is changed.

**Main Success Scenario:**

1. The user selects a visualization or a data point within it and indicates to view its source.
2. The system finds the stored records that produced the selection.
3. The system displays the records according to the "Source display strategy" in the Associated Information of this use case.
4. The user reviews the records.
5. Use case ends.

**Extensions:**

- **2a. The underlying records no longer exist (for example, the dataset was deleted):**
    - 2a1. The system alerts the user that the source data is unavailable and that the visualization should be recreated.
    - 2a2. The user either chooses `UC-FEAT-create-visuals`: Create visualizations from imported data, or terminates the use case.
- **2b. The selection is backed by more records than fit on one screen:**
    - 2b1. The system displays the records in pages and shows the total count.
    - 2b2. The flow rejoins at step 4.
- **4a. The user selects a single record:**
    - 4a1. The system displays all stored fields for that record and its source file.
    - 4a2. The flow returns to step 4.

**Priority:** Very High
**Frequency of Use:** Frequent; every time the user checks a visualization before posting.
**Business Rules:** `BR-evidence-based-analysis`, `BR-data-driven-insights`, `BR-no-data-alteration`

**Associated Information:**

Source display strategy: for each record, the record identifier (such as application number), the fields used in the visualization, the source file name, and the import date (`DI-source-tracking`).

Sort criteria: source file, then record identifier, ascending.

Failure handling: this use case only reads data. If execution fails, nothing is changed and the system shows an error.

**Related Use Cases:** `UC-FEAT-create-visuals`: Create visualizations from imported data; `UC-FEAT-query-ai`: Ask AI assistant.
**Assumptions:** none
**Open Issues:** none

---

### UC-FEAT-export-visuals: The user exports visualizations for a post

**UC ID and Name:** `UC-FEAT-export-visuals`: Export visualizations
**Created By:** Tanner Temple
**Date Created:** 2026-10-26
**Primary Actor:** User
**Secondary Actors:** none
**Trigger:** The user indicates to export visualizations.
**Description:** The user exports one or more staged visualizations so they can be copied into posts and the client's website. Each export is labeled so a reader who never uses the app can understand it.

**Preconditions:**

- PRE-1. The desktop app is running.
- PRE-2. At least one visualization is staged for export (`UC-FEAT-create-visuals`).

**Postconditions:**

- POST-1. Each selected visualization is saved as a file in the chosen location.
- POST-2. Each exported visualization shows its title, data source, date range, and generation date.

**Main Success Scenario:**

1. The user indicates to export visualizations.
2. The system displays the staged visualizations.
3. The user selects one or more visualizations and a save location, and confirms.
4. The system validates that the save location is writable.
5. The system writes each selected visualization to a file, labeled with its title, data source, date range, and generation date.
6. The system confirms which files were saved and where.
7. Use case ends.

**Extensions:**

- **3a. The user cancels:**
    - 3a1. The system exports nothing and the use case ends.
- **4a. The save location is not writable or does not have enough space:**
    - 4a1. The system alerts the user and asks for a different location.
    - 4a2. The flow returns to step 3.
- **5a. One or more visualizations fail to export:**
    - 5a1. The system continues exporting the rest.
    - 5a2. The system lists which visualizations could not be exported.
    - 5a3. The flow rejoins at step 6.
- **5b. A file with the same name already exists:**
    - 5b1. The system asks the user to overwrite it or keep both.
    - 5b2. The flow continues at step 5.

**Priority:** High
**Frequency of Use:** Weekly; once or more per post.
**Business Rules:** `BR-evidence-based-analysis`

**Associated Information:**

| Property name | Data type | Validation rule | Security or access concerns | Glossary reference |
|---|---|---|---|---|
| visualizations | List | Required; one or more staged visualizations | none; local desktop app | Visualization |
| save location | Folder path | Required; must be writable | none | none |

Failure handling: exporting does not change stored data. Files already written stay in place if a later export fails.

**Related Use Cases:** `UC-FEAT-create-visuals`: Create visualizations from imported data.
**Assumptions:** none
**Open Issues:**

- Which export file format(s) are required (`OI-2`).

---

## Working these with your agent

_[Delegate: drafting the main success scenario once you have the trigger and the goal; proposing extensions you have not thought of, which it is genuinely good at; turning a filled-in use case into a first set of test cases; checking that every `BR-*` you cite exists in [business-rules.md](business-rules.md).]_

_Keep human: whether this is one use case or three, what the priority is, and whether an extension the agent proposed is a real path in your client's business or a generic one it has seen elsewhere. "The system handles concurrent edits" is a real requirement for some projects and invented complexity for others, and only you have met the client._

_The verification that catches the most: read the main success scenario aloud to someone who has not read the document, and stop wherever they ask a question. Every question is a missing step or a missing extension._

_**Checklist for each use case:** Does the name start with a verb? Can the system test every precondition? Does every step alternate actor and system? Is there at least one extension per step that can fail? Does every business rule appear as an identifier only? Could a tester write test cases from this without asking you anything?_
