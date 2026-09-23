# Business Rules

**Project:** USPTO Patent Intellignece
**Team:** 6
**Client:** Malachi from Ipelint
**Version:** 0.1

---

_**How to use this template.** Instructions appear in italic square brackets. Fill in underneath them and leave them in place until the document is stable._

_**What a business rule is.** A corporate policy, a government regulation, a law, an industry standard, or a computational formula. Business rules are a rich source of requirements, because they dictate properties your system must have in order to conform to them._

_**What a business rule is not: a software requirement.** This is the distinction students get wrong, so read it twice. A rule is a property of the **business**. It exists whether or not your software does, it was true before you arrived, and it will still be true if the project is cancelled. "A student may only submit a peer evaluation during an active week" is a rule the course had before anyone wrote code._

_What belongs to your software is the **enforcement** of that rule, and that is a functional requirement, written in the specification and cited back here. Keeping the two apart is what lets you answer the question that comes up every semester: "who decided this, and can we change it?" If it is a rule, the client's organization decides and you comply. If it is a requirement, your team decides and you can negotiate._

## How to hear one in a meeting

_[Rules almost never arrive announced. They surface in the middle of a story about something else, usually in one of these shapes:]_

- _"Must comply with..."_
- _"Only `<someone>` may `<do something>`"_
- _"If `<condition>`, then `<something happens>`"_
- _"Must be calculated according to..."_
- _"...unless it has been more than a year."_

_Examples of a client stating a rule without knowing it: "A new client must pay 30 percent of the estimated consulting fee and travel expenses in advance." "Time-off approvals must comply with the company's vacation policy."_

_When you hear one, write it down in the meeting. You will not reconstruct it afterward, and the exact wording matters because the rule is someone else's sentence, not yours._

## The five shapes a rule takes

_[Useful for recognizing rules, not for organizing this document. Sections below are grouped by topic, not by these categories.]_

| Shape | What it does | Example |
|---|---|---|
| **Fact** | States something always true about the business | Every senior design team belongs to exactly one course section. |
| **Constraint** | Restricts what may be done, or by whom | Only a course admin may create a course section. |
| **Action enabler** | Triggers an action when a condition holds | If a student has not completed safety training in 12 months, the request is refused. |
| **Inference** | Derives a new fact from known facts | A team with no submissions for two consecutive weeks is at risk. |
| **Computation** | Defines how a value is calculated | The peer evaluation score is the mean of all scores received that week. |

_Computations are the ones teams forget are rules. A formula the client uses today is a rule you must reproduce exactly, not a design decision you get to make. Ask for the spreadsheet._

## What a rule turns into

_[One rule usually propagates into several requirements of different kinds. This is why the document exists as its own artifact rather than being scattered through the specification.]_

| Requirement type | How the rule shows up | Example |
|---|---|---|
| Business requirement | A regulation drives a business objective | The system must enable compliance with all federal and state chemical reporting regulations within five months. |
| User requirement | A privacy policy dictates who may do what | Only laboratory managers may generate chemical exposure reports for anyone other than themselves. |
| Functional requirement | A company policy becomes system behavior | If an invoice is received from an unregistered vendor, the system shall email the vendor the supplier intake form and the W-9. |
| Quality attribute | A safety regulation becomes a checked property | The system must maintain safety training records and check them before a user can request a hazardous chemical. |

## Identifiers and traceability

_Each rule carries a stable `BR-<slug>` identifier, a name-based slug coined from the rule's gist: `BR-active-weeks`, `BR-section-admin-only`, `BR-artifact-key-unique`. Never renumber, rename, or repoint one. The thematic grouping into sections below is organizational only and does not affect a rule's identity, so moving a rule between sections is free and renaming it is not._

_**Cite rules, do not copy them.** When a use case is governed by a rule, its Business Rules field carries the identifier only, never the rule's text. One rule, one home. A rule copied into three use cases will be updated in one of them._

_A rule may cite another rule by identifier where one depends on another._

## Every rule needs a source

_[The column teams leave blank, and the one that matters most. For each rule, record where it comes from: a named policy document, a regulation, a page of the client's handbook, or the person who told you and the date.]_

_A rule you cannot attribute is usually not a rule. It is your team's design decision wearing a rule's clothes, and it belongs in the specification where it can be argued with. The test: if you asked your client to change it tomorrow, who would have to approve? If the answer is "you", it was never a rule._

_Where a rule is expected to change, say so and say when. Rules change on the business's schedule, not on yours._

## Where your AI teammate helps, and where it is dangerous

_[Delegate: turning your meeting notes into candidate rules, spotting sentences in a transcript that have the shape of a rule, and finding use cases in your specification that a given rule ought to govern but does not cite.]_

_**Do not let it invent rules.** This section is the single most dangerous place in your requirements for fabricated content, because an invented rule reads exactly like a real one. "Passwords must be at least 8 characters." "Records must be retained for 7 years." Both are plausible, both are common, and neither is your client's policy unless your client said so. A fabricated rule then propagates into functional requirements, tests that pass, and code that enforces something nobody asked for._

_The Source column is the defense. Every rule traces to a document or a person, or it does not go in the file. When your agent proposes a rule, the only question is: who told us this?_

## Revision History

| Date | Version | Description | Author |
|---|---|---|---|
| 2026-09-23 | 0.1 | Initial rules from the client brief and first client meeting | Koen |

---

## 1. Introduction

### 1.1 Purpose

_[One paragraph: this document collects the policies, regulations, standards, and formulas that govern the business your software operates in, so the specification can cite them rather than restate them.]_

This document captures the business rules, industry practices, data relationships, and operational constraints that govern the patent analytics domain for the USPTO visualization platform. These rules originate from patent prosecution processes, USPTO data structures, and the client's professional workflow, allowing software requirements to reference them without restating them.

### 1.2 Scope

_[Which parts of the client's business these rules cover, and which are out of scope. If your client's organization has rules that your system does not touch, say so here rather than silently omitting them.]_

These rules cover the collection, analysis, historical storage, linkage, and visualization of publicly available USPTO patent-related datasets, including office action, patent grant, and litigation data. The document also covers patent prosecution concepts that influence analysis. Internal software architecture decisions, technology choices, user interface design decisions, and implementation details are outside the scope of this document.

## 2. Rules

_[Group rules under topic headings that fit your project. The Project Pulse headings are one example, not a required set: Course Administration, Teams and Assignment, Access and Ownership, Identity and Uniqueness, Editing and Locking, Deletion Integrity, Review and Submission._

_Format each rule as a bold identifier, the rule in one sentence, then its source. Worked examples:]_

### 2.1 Patent Prosecution and Office Actions
- **`BR-art-unit-assignment`:** Every patent application is assigned to an art unit for examination by subject-matter specialists.
  **Source:** Client interview, background explanation, 2026-09-17.
- **`BR-office-action-issued`:** Office action is the process of determing whether a patent is to be accepted or rejected. 
  **Source:** Client interview, patent prosecution process explanation, 2026-09-17.
- **`BR-102-rejection`:** A Section 102 rejection indicates that prior art exists that prevents the claimed invention from being considered novel.
  **Source:** Client interview, patent prosecution explanation, 2026-09-17.
- **`BR-103-rejection`:** A Section 103 rejection indicates that an invention is considered obvious based on prior art.
  **Source:** Client interview, patent prosecution explanation, 2026-09-17.
- **`BR-112-rejection`:** A Section 112 rejection concerns deficiencies in the specification or claims of a patent application.
  **Source:** Client interview, patent prosecution explanation, 2026-09-17.
- **`BR-double-patenting`:** A double patenting rejection indicates that multiple patentable concepts should be separated rather than protected in a single patent.
  **Source:** Client interview, patent prosecution explanation, 2026-09-17.

### 2.2 Patent Data Sources
- **`BR-weekly-uspto-publication`:** USPTO office action data is distributed in periodic ZIP-file releases.
**Source:** Client interview, USPTO data discussion, 2026-09-17.
- **`BR-weekly-office-action-data`:** Office action datasets are published weekly and serve as a primary source of patent prosecution information.
**Source:** Client interview, USPTO data discussion, 2026-09-17.
- **`BR-separate-dataset-domains`:** Patent prosecution, patent grant, and litigation information are maintained as separate datasets.
**Source:** Client interview, workflow discussion, 2026-09-17.
 
### 2.3 Patent Record Relationships
- **`BR-cross-record-linkage`:** Patent applications, granted patents, and litigation records may refer to the same invention lifecycle and therefore have meaningful relationships that must be traceable.
**Source:** Client interview, workflow discussion regarding patent history, 2026-09-17.
- **`BR-patent-lineage`:** Patent family and child-patent relationships are important components of patent history analysis.
**Source:** Client interview, workflow discussion, 2026-09-17.
 
### 2.4 Historical Analysis
- **`BR-historical-analysis`:** Patent analysis may rely on historical records collected across multiple years.
**Source:** Client interview, historical reporting discussion, 2026-09-17.
- **`BR-litigation-history-window`:** Litigation datasets may contain approximately twenty-one years of historical records.
**Source:** Client interview, dataset discussion, 2026-09-17.
- **`BR-prosecution-history-window`:** Patent prosecution datasets commonly contain approximately three to four years of historical records.
**Source:** Client interview, dataset discussion, 2026-09-17.
 
### 2.5 Analytics and Reporting
- **`BR-evidence-based-analysis`:** Analytical conclusions must be supported by evidence contained within the underlying patent data.
**Source:** Client statement: "using concrete evidence from the given numbers," 2026-09-17.
- **`BR-data-driven-insights`:** Analytical observations must be derived from patent data rather than unsupported assumptions.
**Source:** Client interview, discussion of analysis accuracy, 2026-09-17.
- **`BR-rejection-distribution-metric`:** The distribution of office actions by rejection category is a meaningful patent-analysis measure.
**Source:** Client examples of desired analyses, 2026-09-17.
- **`BR-pendency-trend-metric`:** Patent pendency over time is a meaningful patent-analysis measure.
**Source:** Client examples of desired analyses, 2026-09-17.
 
### 2.6 Data Jurisdictions
- **`BR-uspto-primary-source`:** USPTO data serves as the primary source of patent analysis.
**Source:** Client interview, project scope discussion, 2026-09-17.
- **`BR-international-expansion`:** Patent analysis may be expanded to include international patent datasets such as those provided by the European Patent Office and Chinese patent authorities.
**Source:** Client interview, future roadmap discussion, 2026-09-17.
- **`BR-jurisdictional-differences`:** Patent systems from different jurisdictions are governed by different legal frameworks and must not be treated as equivalent.
**Source:** Client statement regarding European patent data and differing laws, 2026-09-17.

_[That third entry is deliberate. Flag rules you are not sure about rather than dropping them; deciding whether something is a rule or a requirement is a conversation to have with your client, and it is worth having.]_

_**Checklist:** Does every rule have a source? Could your client change it without asking you? Is it stated as one sentence about the business, rather than as a sentence about your software? Does any use case cite it, and if none does, is that correct?_
