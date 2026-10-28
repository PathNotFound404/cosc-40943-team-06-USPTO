# Open Issues

**Project:** USPTO Patent Intelligence
**Team:** 06

---

_**What this file is.** Every question about the project that you cannot answer yet, in one place, with the name of the person who can answer it. It is the shortest document in `docs/requirements/` and the one your client meetings run on._

_**Why it exists.** A draft specification with confident guesses in the gaps is more dangerous than one with holes in it, because nobody can tell the guesses from the facts. Writing "we do not know" is not an admission of failure in week 3, it is the correct state. What fails is knowing and not writing it down._

_**Where entries come from.** Three places, and all three are routine:_

- _Drafting a section of [vision-and-scope.md](vision-and-scope.md) and hitting something the client brief does not say._
- _Your agent's list. When you ask it to draft a section, ask it to list every question it could not answer from the material you gave it. Its list is longer than yours and it is not embarrassed to ask obvious things._
- _The meeting itself. Your client says something that contradicts your notes, or answers a question with "I would have to check"._

_**How they leave.** Answered in a client meeting, in Slack, or by reading a document. Record the answer and the date, mark it resolved, and put the substance where it belongs (an objective, a term in the [glossary](project-glossary.md), a business rule). This file is a queue, not a home: an answer that stays here has not been filed._

_**Identifiers here are numbers**, `OI-1` upward, and that is deliberate. Numbers are fine for a list that only ever grows at the bottom and gets cited lightly. The slug convention in [vision-and-scope.md](vision-and-scope.md) exists for identifiers that get **reordered** or **cited often**, which is not this list._

## Before a client meeting

_[Sort the open list by what it costs you to stay wrong, not by what is easy to ask. You will get through fewer questions than you plan to. Take the ones where a wrong guess sends the whole team down the wrong path for a month, and leave the ones you can settle by reading a document or trying the client's current tool yourself.]_

_[Send the shortlist to your client the day before. A client who has seen the questions arrives with answers instead of promises.]_

## Open

| ID | Question | Why it matters | Who can answer | Raised |
|---|---|---|---|---|
| OI-1 | Which metrics and visualization types are required in release 1.0? | Blocks the visualization scripts in `UC-FEAT-create-visuals`. | Client | 2026-09-25 |
| OI-2 | Which export file format(s) must visualizations support (for example PNG, SVG, PDF, CSV)? | Blocks `UC-FEAT-export-visuals` and staging in `UC-FEAT-create-visuals`. | Client | 2026-09-25 |
| OI-3 | Does the user choose visualization types, or always receive all of them? | Changes steps 3-4 of `UC-FEAT-create-visuals`. | Client | 2026-09-25 |
| OI-4 | What column naming convention should cleaned data use? | Blocks the cleaning script in `UC-FEAT-clean-data`. | Team | 2026-09-25 |
| OI-5 | Does null handling remove whole records or only null values, and does the user see a count of what was removed? | Changes results and counts in `UC-FEAT-clean-data`; risks `BR-no-data-alteration`. | Client | 2026-09-25 |
| OI-6 | Which exact bulk file formats must be supported (ZIP of XML, JSON, other)? | Blocks validation in `UC-FEAT-decompile-files`. | Client sample data | 2026-10-26 |
| OI-7 | When the USPTO's rejection tag and the office action letter text disagree, which one should charts count by default? | In the 2026-10-18 sample, 2,087 records cite §102 in the letter text but are not tagged §102, so a tag-based chart undercounts §102 by more than three times. Blocks the rejection metrics in `UC-FEAT-create-visuals` and `FR-CHART-counted-field`. | Client | 2026-10-27 |
| OI-8 | Should pendency be first-action pendency (filing to first office action) or total pendency (filing to grant or abandonment)? | Blocks the pendency metric (`BR-pendency-trend-metric`, SRS 7.2 and 7.3). Total pendency also needs grant data, which is out of scope. | Client | 2026-10-26 |
| OI-9 | May published content show figures for individual examiners (identified by employee number), or only for art units and Technology Centers? | Decides whether examiner-level charts exist at all (`DI-identifiable-people`, `RI-Examiner-Identification`). | Client | 2026-10-26 |
| OI-10 | Are grant and litigation data part of release 1.0, or only office action data? | Vision and scope 4.3 puts them out of scope; if the client needs them, `FEAT-Link-Datasets` moves into the MVP and the schedule is at risk (`AS-release-scope`, `AS-office-action-data-sufficient`). | Client | 2026-10-26 |
| OI-11 | How much disk space can the application use on the client's 2 TB drive? | Sets `SCA-storage-limit`, and with it how many years of history can be kept with the full letter text (architecture `RISK-storage-growth`). | Client | 2026-10-26 |
| OI-12 | Is a paid Apple developer account (for code signing) acceptable, or must the app stay unsigned? | Unsigned apps need an extra "Open anyway" step on first launch, which may fail `USE-zero-config`; paying conflicts with `CO-zero-recurring-cost` (SRS 11, architecture `RISK-unsigned-app`). | Client | 2026-10-26 |
| OI-13 | Are the proposed targets acceptable: under 1 hour of hands-on time per weekly file (`USE-weekly-data-time`), overnight processing within 8 hours (`PER-weekly-processing`), and charts updating within 5 seconds (`PER-dashboard`)? | These numbers were proposed by the team, not given by the client; tests will be written against them. | Client | 2026-10-26 |
| OI-14 | Can the client send two or three more weekly files from different periods, including any in ZIP or XML form? | Only one sample exists; format differences between weeks or years would break import (`AS-weekly-file-format`, architecture `RISK-format-drift`). Related to `OI-6`. | Client | 2026-10-27 |
| OI-15 | When will the client send the process video promised at the first meeting? | The as-is and to-be process flows (vision and scope 1.2, 2.5) are drawn from the interview only and need checking against it. | Client | 2026-09-17 |
| OI-16 | Is it correct that no formal accessibility standard (such as WCAG) is required? | Confirms `USE-accessibility`; a required standard would add UI work and tests. | Client | 2026-10-26 |
| OI-17 | What are the minimum macOS version and minimum hardware the application supports? | Sets `OE-desktop-os` and `OE-minimum-hardware`, and the PyInstaller build target. | Team | 2026-10-26 |
| OI-18 | Who produces wireframes for the views in `UI-main-views`, and where are they kept? | `UI-wireframes` has no link; the UI design for each use case has nothing to start from. | Team | 2026-10-26 |

Not logged, because the feature is deferred: model licensing (`CO-model-licensing`) and which USPTO API provides office action data (`DE-uspto-api`). Log them when AI or the API comes into scope.

## Resolved

| ID | Question | Answer | Answered by | Date | Filed in |
|---|---|---|---|---|---|
