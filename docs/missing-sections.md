# Documentation Gap Report

**Project:** USPTO Patent Intelligence · **Team:** 06
**Checked:** 2026-10-26, against `main` @ `a7980f0` (SRS v1.2)

**Legend:** **Empty** means nothing is written there, or it only has the template's example. **Partial** means something is written but parts are still missing or marked TBD. **Leftover** means template example text that should be deleted.

## Summary

| File | Status |
|---|---|
| `README.md` | Title only |
| `docs/design/architectural-design.md` `Cody` | Not started |
| `docs/traceability.md` | Not started |
| `docs/Requirements/OPEN-ISSUES.md` | Not started |
| `docs/Requirements/use-cases.md` `Tanner` | Partial |
| `docs/Requirements/vision-and-scope.md` `Turner`| Partial |
| `docs/Requirements/project-glossary.md` `Turner`| Partial |
| `docs/Requirements/software-requirements-specification.md` `Edwin` | Mostly done (v1.2); §5.2 still empty |
| `docs/team-contract.md` | Partial |
| `docs/Requirements/client-interview-2026-09-13.md` | Partial |
| `docs/Requirements/business-rules.md` `Koen`| Filled in, but content is duplicated |
| `docs/Requirements/napkin.md` | Complete |
| `docs/Requirements/client-interview-guide.md` | Blank template (expected) |

---

## README.md
- [ ] Only the heading `# cosc-40943-team-06-USPTO` exists. Needs a project description, setup instructions, and doc links. `MNT-developer-readme` in the SRS requires build/run instructions.

## docs/design/architectural-design.md (not started)
- [ ] Header: Project, Team, Client: Empty
- [ ] Revision History: date and author: Empty
- [ ] 1.1 Requirements overview: Empty (CP1)
- [ ] 1.2 Quality goals: Empty, example only (CP1). Candidates from the SRS: `SAF-evidence-required`, `ROB-bad-input`, `SEC-no-data-egress`, `CO-single-maintainer`
- [ ] 1.3 Stakeholders: Empty (CP1)
- [ ] 2 Architecture Constraints: Empty (CP1). The SRS now has `CO-*` and `OE-*` IDs to list
- [ ] 3 Context and Scope (C4 context diagram): Empty, example only (CP1)
- [ ] 4 Solution Strategy: Empty, example only (CP1)
- [ ] 5.1 Containers (C4 container diagram): Empty, example only (CP1)
- [ ] 5.2 Use case areas and components: Empty, example only (CP1)
- [ ] 6 Runtime View: Empty (CP2)
- [ ] 7 Deployment View: Empty (CP3)
- [ ] 8.1 Security (trust boundary, authentication, authorization, sensitive data): Empty (CP1/CP2)
- [ ] 8.2 Other concepts, one subsection each: error handling, time and time zones, API conventions, code conventions, validation, configuration and secrets, logging, persistence and concurrency, auditing, testing: Empty (CP1)
- [ ] 9.1 Architecturally significant requirements: Empty, example only (CP1)
- [ ] 9.2 Key decisions (required: `KD-deployment-shape`): Empty, example only (CP1)
- [ ] 10.1 Quality requirements overview (link to SRS §9): Empty
- [ ] 10.2 Quality scenarios: Empty, example only (CP2)
- [ ] 11 Risks and Technical Debt: Empty, example only (CP2)
- [ ] 12 Glossary (link): Empty

## docs/traceability.md (not started)
- [ ] Header: Project, Team, Last checked: Empty
- [ ] §1 Feature to use case area: Empty (Project Pulse rows only)
- [ ] §2 Business rule to what enforces it: Empty (Project Pulse rows only)
- §3 is not due until week 8 and should be left as is

## docs/Requirements/OPEN-ISSUES.md (not started)
- [ ] Open table: Empty (template row OI-1 only). The other docs have many TBDs to move here; see "TBD items to move into OPEN-ISSUES" below
- [ ] Resolved table: Empty (example row OI-0 only; delete it)
- [ ] Header typo: "Intelllignece"

## docs/Requirements/software-requirements-specification.md (v1.2)
- [ ] Revision History: dates say 2027 instead of 2026 and are still in placeholder brackets; typo "secttions"
- [ ] 2.1 Product perspective: the architecture context diagram link is TBD
- [ ] **5.2 Non-use-case functional requirements: Empty.** `FR-TASK-completion-notice` (cited in §8.5) and `FR-VERIFY-ai-claims` (cited in §9.4) are referenced but never defined
- [ ] 7.1 Business domain model: Leftover Team/Student example diagram still above the real one
- [ ] 7.2 Data dictionary: Partial. Fields are TBD until sample data arrives (`example data/bdr_oa_bulkdata_weekly_2026-10-18.json` is now in the repo, untracked). `actionType` values TBD; pendency formula TBD
- [ ] 8.1 User interfaces: wireframes link TBD
- [ ] 8.4 API document: TBD until code exists
- [ ] §1.1 says "desktop application for macOS" but `OE-desktop-os` says macOS **and** Windows; make them consistent
- [ ] §10 uses `INT-jurisdiction-separation`, but the `INT-` prefix is for interoperability

## docs/Requirements/vision-and-scope.md
- [ ] Identifiers example table: Partial (cells filled with `x`)
- [ ] 1.1 Background: Partial (no description of the business, Step 1; stray `.` line)
- [ ] 1.2 Current Process Flows (As-Is): Partial (one sentence; no mermaid diagram, prose, current tools or pain points)
- [ ] 1.3 References: Empty ("--> Insert Client Brief")
- [ ] 2.2 Business Objectives: Partial (only `BO-Post-Visuals`, no number; the interview baseline is 8 hours per post)
- [ ] 2.3 Success Metrics: Partial (only `SM-Accuracy`; no source, baseline or deadline)
- [ ] 2.4 Vision Statement: Empty template table (the filled version is under "Worked example", and its "The" row is malformed)
- [ ] 2.5 Proposed Process Flows (To-Be): Empty (placeholder note)
- [ ] 2.6 Risks: Partial (one risk named `Cost`; needs an `RI-` slug, probability and impact; more risks needed)
- [ ] 2.7 Business Assumptions and Dependencies: Partial (only `AS-local`)
- [ ] 3.1 Stakeholder Profiles: template row blank; Malachi's row is outside the table
- [ ] 3.3 Alternatives and Competition: template row blank; both rows are outside the table
- [ ] 4.1 Product Perspective: Empty (still the Project Pulse diagram)
- [ ] 4.2 Major Features: table header lists `FEAT-Upload-Zip`, but the list says `FEAT-Intake-Data`
- [ ] 4.3 MVP Scope: Partial (no out-of-scope list; leftover `FEAT-...` template lines)

## docs/Requirements/use-cases.md
- [ ] Header: stray `_` after the project name
- [ ] Revision History row 0.1: date and author placeholders
- [ ] 1.1 Purpose: Empty
- [ ] 1.2 Scope: Empty
- [ ] 3 Use Case List: Empty (template row only)
- [ ] §4: Leftover example `UC-RUB-find-criteria` not deleted; no `##` heading per area
- [ ] Area code: every use case uses `FEAT` as its area; needs real area codes (for example `ING`, `VIS`, `AI`)
- [ ] `UC-FEAT-decompile-files`: Associated Information Empty; Related Use Cases Empty; step 5a2 unnumbered
- [ ] `UC-FEAT-query-ai`: Associated Information Empty; step 7 says "course material"
- [ ] `FEAT-Verify-Source` has no use case of its own
- [ ] No use cases yet for views listed in SRS `UI-main-views`: Export, Patent History, Settings (change AI model), Sources
- [ ] `UC-FEAT-clean-data` cites `BR-no-data-alteration`, which is not defined in business-rules.md

## docs/Requirements/business-rules.md
- [ ] Purpose and Scope paragraphs each appear twice
- [ ] All rules in §2.1–2.6 appear twice (the second copy starts at `BR-art-unit-assignment` after §2.6)
- [ ] `BR-office-action-issued` has two different definitions; pick one. Typo "determing"
- [ ] Duplicate revision history row
- [ ] Missing rule: `BR-no-data-alteration` (cited by a use case)
- [ ] Leftover template text: "That third entry is deliberate…"
- [ ] Header typo: "Intellignece"

## docs/Requirements/project-glossary.md
- [ ] Leftover examples not deleted: Active Week, City-Pair, Weekly Activity Report
- [ ] Revision History date still in placeholder brackets
- [ ] Only 3 terms, not alphabetical (Art Unit, Office Action Data, Grant)
- [ ] Terms used in other docs but not defined: Technology Center, Examiner, Rejection (102 / 103 / 112 / Double Patenting), Pendency, Litigation Case/Data, Patent Family / Lineage, Bulk Data / Weekly ZIP Release, USPTO Open Data Portal, Patent Application, Patent Prosecution, Anomaly

## docs/team-contract.md
- [ ] Title: `<team name>` placeholder
- [ ] §4 Claiming: still template text `<e.g. assign yourself the sub-issue and move the card>`
- [ ] §5 Branch naming: still the template example `feat/42-short-slug`
- [ ] §5 Blocking a merge: placeholder-style wording
- [ ] §6 Additional limits: "to be reviewed"
- [ ] Typos: "Inteligence", `CLAUDE.m`

## docs/Requirements/client-interview-2026-09-13.md
- [ ] "Before you go" checklist: all unchecked
- [ ] §3 Candidate objectives (`BO-*`): Empty
- [ ] §4 How it works today: Empty (waiting on client video and data); Artifacts: pending
- [ ] §15 checklist: all unchecked; "Say what happens next": blank
- [ ] Initial ideas: Empty
- [ ] Disagreements and hesitations: Empty
- [ ] Open questions: Empty

---

## TBD items to move into OPEN-ISSUES.md

| Where | Item |
|---|---|
| SRS 2.3 | `OE-desktop-os`: minimum OS versions; is Windows in scope? |
| SRS 2.3 | `OE-minimum-hardware`: RAM, storage and GPU minimums |
| SRS 2.4 | `CO-model-licensing`: model and runtime licenses |
| SRS 2.5 | `DE-uspto-api`: which API provides office action data |
| SRS 2.5 | `AS-release-scope`: are grant and litigation data in release 1.0? |
| SRS 7.2 | Office action `actionType` values; pendency formula |
| SRS 7.4 | `DI-identifiable-people`: may examiner names appear in published content? |
| SRS 9.1 | `USE-weekly-data-time` target (under 1 hour?); `USE-accessibility` |
| SRS 9.2 | `PER-weekly-processing` (8 hours), `PER-dashboard` (5 seconds), `PER-ai-response` (60 seconds) |
| SRS 9.7 | `SCA-storage-limit`: disk space budget; `INT-export` formats beyond PNG |
| SRS 11 | Code signing vs. `CO-zero-recurring-cost` |
| Use cases | Which metrics and visualization types; export formats; whether the user picks visualization types; column naming convention; null handling |
| Vision 2.5 | To-be process (waiting on client process video) |
