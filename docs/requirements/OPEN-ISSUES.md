# Open Issues

**Project:** USPTO Patent Intelllignece
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

## Resolved

| ID | Question | Answer | Answered by | Date | Filed in |
|---|---|---|---|---|---|
| OI-0 | _[Example row, delete it]_ | _[What we were told]_ | _[Name]_ | _[YYYY-MM-DD]_ | _[`BO-grading-time`, or the glossary term, or the section]_ |
