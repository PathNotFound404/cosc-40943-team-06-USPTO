# Traceability Matrix

**Project:** _[Your project name]_
**Team:** _[Team NN]_
**Version:** 0.1
**Last checked:** _[YYYY-MM-DD, by whom]_

---

_**How to use this template.** Instructions appear in italic square brackets. Fill in underneath them and leave them in place until the document is stable._

_**What this file is.** The map of your project, from the reason something exists to the thing that does it. Every other document owns its own contents; this one owns the **links between them**, so nobody has to restate anything to find out what connects to what._

_**Why it exists before any code does.** The question it answers in week 4 is "did we specify everything we promised, and nothing we did not?" The question it answers in week 12 is "this broke, what was it supposed to do, and who asked for it?" Those are the same question, and the file that answers the second one is the file you started in week 4. Starting it later means reconstructing links from memory, which is the same work done worse._

_**It grows.** Week 4 fills in two tables. Week 8 adds the columns for design, code, and tests once those exist, and the tables below leave room for them. Do not add empty columns now._

_**Run the checks by hand this week.** Each table below ends with two checks. They are cheap, and they fail loudly. Hand the whole file to your agent and ask it to run them, then verify what it tells you, because a check reported as passing by the thing that also wrote the table is not evidence._

---

## 1. Feature to use case area

_[Your vision and scope lists product **features** (`FEAT-<slug>`), each a capability a stakeholder can see. Your use case file groups behavior into **use case areas** (`UC-<AREA>-*`). This table connects them, and it is where **business objectives attach**: the objective hangs on the feature, and every use case underneath inherits it. That is why the objective is named here once, rather than repeated on forty use cases._

_Features and areas are deliberately many-to-many. A feature that lands on exactly one area is probably too narrow, and a feature that reads "create, edit, and delete X" is a list of use cases wearing a feature's clothes._

_Worked example, from Project Pulse:]_

| Feature | Business objectives | Use case areas |
|---|---|---|
| `FEAT-performance-tracking` | `BO-PERF-instructor-efficiency`, `BO-PERF-student-participation` | `WAR`, `EVA` |
| `FEAT-administration` | (enabling, serves no objective directly) | `SEC`, `TEA`, `STU`, `INS`, `ACC`, `RUB` |

_[An enabling feature that serves no measurable objective on its own says so, as the second row does. That is different from forgetting to fill the column in.]_

**Checks.**

1. **Every feature has at least one area.** A feature with none means your vision promises something nobody has specified.
2. **Every area is reached by a feature.** An area no feature points at means you have use cases no stakeholder asked for.

---

## 2. Business rule to what enforces it

_[A business rule is a property of your client's business, so it has no implementation of its own. What it has is a set of requirements that enforce it, and this table is how you find them. Rules are **cited, never restated**: the rule's text lives in `business-rules.md` and nowhere else, and this table holds only the identifier and the links._

_The **Source** column is duplicated here from `business-rules.md` on purpose, and it is the one exception in this file. It is the column reviewers and clients actually read, and a rule whose source is one click away is a rule nobody checks._

_Worked example, from Project Pulse:]_

| Business rule | Source | Enforced by |
|---|---|---|
| `BR-evaluation-submission-window` | Not recorded | `UC-EVA-submit-evaluation` step 7 and extension 1b |
| `BR-section-admin-only` | Not recorded | `UC-RUB-assign-rubric`, `UC-SEC-create-section`, `UC-SEC-edit-section`, `UC-SEC-setup-active-weeks` |

**Checks.**

1. **Every rule is enforced by something.** A rule with an empty third column is a policy your software ignores. That may be the right answer, and it is only the right answer if you decided it on purpose. Write the decision in `OPEN-ISSUES.md` rather than leaving the cell blank.
2. **Every requirement that cites a rule cites one that exists.** Search your use cases and specification for every `BR-` identifier and confirm each one is defined in `business-rules.md`. This is the check that catches a draft citing `BR-late-penalty` because a late penalty is the kind of thing a course usually has. A generated document cites plausible identifiers with complete confidence, and nothing else in your process will notice.

---

## 3. From here (week 8)

_[Leave this section as it is until week 8. It says what the two tables above grow into, so that nobody restructures the file in the meantime._

_In week 8 the spine extends past the use case: **business objective → feature → use case area → use case → design → code → test.** A third table arrives with one row per use case and columns for the design element, the source files, and the tests, tracked as two separate states, built and verified, so that a use case which is built but untested stays visibly unverified rather than being absorbed into a single "done".]_

---

## Working this document with your agent

_[Delegate: running both checks and reporting what fails; finding every `BR-`, `FEAT-`, and `UC-` identifier cited anywhere in `docs/` and listing the ones with no definition; regenerating the second table from the Business Rules fields of your use cases after you have edited them._

_Keep human: whether an area with no feature is a missing feature or a use case that should not exist, and whether an unenforced rule is an oversight or a decision. Both are questions about your client's business, and the answer is not in your repository._

_**The specific failure to watch for:** an agent asked to "fill in the traceability matrix" produces a complete, well-formed table in which every cell is populated and some of the links are invented. A blank cell is information. A confidently wrong link is worse than no link, because it makes the check pass. Verify every row you did not write yourself by opening the document at the other end.]_
