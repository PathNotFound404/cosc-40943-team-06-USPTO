# Project Glossary

**Project:** USPTO Patent Intelligence 
**Team:** 06
**Client:** Malachi Hernandez 
**Version:** 0.3

---

_**How to use this template.** Instructions appear in italic square brackets. Fill in underneath them and leave them in the file until the document is stable._

_**What this document is for.** Every project has words that mean something specific inside the client's organization and something else outside it, or nothing at all. This file fixes one word to one concept, and commits the team, the client, and the AI teammate to using it. That shared vocabulary is called a **ubiquitous language**: the same term in the client conversation, in the vision and scope, in the use cases, in the class names, and in the database columns._

_**Why the glossary is the first artifact you write and the last one you finish.** It is the cheapest document to start, because your client hands you the terms in the first meeting whether you ask or not, and it is the one that keeps paying: every later document cites it instead of redefining things._

## Why this matters when an agent writes your code

_[Read this once, then delete this section when the document goes stable.]_

_If two words in your project mean the same thing and nothing says so, your team will use both. So will your agent. You will end up with a `Team` class and a `Group` table, a `submitReport` endpoint and a `war_entry` record, and every one of those pairs is a bug waiting for the week you try to join them._

_An agent cannot resolve this on its own. Asked to add a feature, it reads what is in the repository and imitates it. If the repository is inconsistent it will faithfully reproduce the inconsistency, and it will invent a plausible synonym for anything the repository never names. A glossary in the repository is the only thing that stops it, because the repository is the whole of the agent's memory of your project._

_The other half is human. When your client says "cycle" in one sentence and "sprint" in the next, that is your signal to ask which one they mean, in the meeting, while they are in front of you. An agent reading the transcript later cannot ask._

## The entries that earn their place

_[The temptation is to define words your teammates already know. Skip those. The entries worth writing are:]_

- _**Terms two stakeholders use differently.** The highest-value entry in any glossary. In airline statistics, the International Civil Aviation Organization says **city-pair** and the International Air Transport Association says **O and D**, for the same thing; the two bodies also say **traffic by flight stage** and **segment traffic** for another. A team that misses this builds a report that silently mixes them._
- _**Terms that sound generic but are not.** "Active", "submitted", "complete", "week". Ask what makes a record active and you often find a business rule nobody had stated._
- _**The client's acronyms**, spelled out, including the ones they use so fluently they have forgotten they are acronyms._
- _**Terms you invented** that the client does not use. Record them, then consider dropping them in favor of the client's word._

_Ask the client directly: "Is there a word your team uses here that I would not guess the meaning of?"_

## Conventions

_[The **term itself is the identifier**. There is no separate numbering scheme, because a glossary entry already has a unique, meaningful name: the word. Cite a term by writing it, and keep the spelling identical everywhere it appears._

_Rules:_

- _One entry per concept. If two words mean the same thing, pick one, define it, and list the other as a synonym under it rather than giving it its own entry._
- _Alphabetical order, so a reader can find a term without searching._
- _Define the concept, not the implementation. "A weekly record of what a student did" is a definition; "a row in the `war` table" is not._
- _Use the client's word when the client has one. You are joining their world, not renaming it._
- _If a term has a meaning outside this project that differs from the one here, say so explicitly.]_

## Revision History

| Date | Version | Description | Author |
|---|---|---|---|
| 2026-09-24 | 0.1 | Initial terms from the client brief and first client meeting | Cody Pinkston |
| 2026-10-27 | 0.2 | Removed template examples; alphabetized; added terms used in other documents and in the 2026-10-18 sample weekly file | Turner DeMott |
| 2026-10-28 | 0.3 | Added Visualization, which the use cases cite as a glossary term; corrected Art Unit and Work Group, since 22 sample records break the work group numbering rule | Cody Pinkston |

---

## Definitions

_[One `###` heading per term, alphabetical. Follow the heading with a definition of one to three sentences. Add **Synonyms**, **Not to be confused with**, or **Source** lines where they help. Where a term only makes sense with an example, give one.]_

### Anomaly

A number that is unusual compared with what would be expected, for example an art unit whose share of §103 rejections this week is far outside its own history. An anomaly is a prompt for a closer look, not a finding of wrongdoing.

**Not to be confused with:** fraud. The client brief mentions "fraud/anomaly detection", but the application labels unusual patterns only as anomalies (`SAF-no-accusation` in the SRS).

**Source:** client project brief

### Application Number

The number the USPTO assigns to a patent application when it is filed, for example `13886682`. It identifies the application throughout prosecution and is the key that links office actions for the same application.

**Not to be confused with:** the patent number, which is assigned only if the application is granted, and the litigation case number. Linking these three is the core of [Cross-Record Linkage](#cross-record-linkage).

**Source:** `patentApplicationNumber` in the 2026-10-18 sample weekly file

### Art Unit

A specialized group of patent examiners within the USPTO, organized around one field of technology so its examiners build expertise in that field. Identified by a four-digit number; the first two digits give its [Technology Center](#technology-center), and the first three usually give its [Work Group](#work-group) (see that entry for exceptions). For example, art unit 3783 is in work group 3780 and Technology Center 3700.

In the client's words: the group of people who review your patent, including the patent examiner, with subject-matter expertise, who look at prior knowledge before granting.

**Synonyms:** Group Art Unit, GAU (`groupArtUnitNumber` in the data)

**Source:** USPTO website; client interview 2026-09-17. The 2026-10-18 sample contains 524 art units.

### Cross-Record Linkage

Identifying records in separate datasets (office action, grant, litigation) that belong to the same invention, so one invention's history can be followed from filing to litigation. The datasets use different numbers, so the link has to be made through shared identifiers rather than assumed.

**Source:** client interview 2026-09-17; `BR-cross-record-linkage`

### Document Code

The USPTO's short code for the type of document in an application's file. The weekly office action file contains two:

- **CTNF:** non-final rejection (see [Office Action](#office-action))
- **CTFR:** final rejection

**Source:** `documentCode` in the 2026-10-18 sample weekly file (5,160 CTNF and 3,507 CTFR records). Other codes may appear in other files.

### Examiner

A USPTO employee who reviews patent applications against the legal requirements and issues office actions. Every examiner belongs to one [Art Unit](#art-unit).

**Note:** In the weekly office action file, examiners are identified by an employee number, not by name. That number still identifies a real person, so how examiner-level figures may be published is an open question (`DI-identifiable-people`).

**Source:** USPTO website; `examinerEmployeeNumber` in the 2026-10-18 sample (4,882 distinct examiners)

### Final Office Action

An office action that closes the current round of examination. To continue, the applicant must file a request for continued examination, appeal, or otherwise respond under stricter limits than after a non-final action.

**Synonyms:** final rejection, CTFR (see [Document Code](#document-code))

**Not to be confused with:** a final decision on the application. An application can still be granted after a final office action.

**Source:** USPTO website

### Grant 

The point at which a patent application has met all legal requirements and is officially issued as an enforceable patent, receiving a patent number.

Unlike a published patent application, a granted patent gives the owner the legal right to stop others from making, using, selling, or importing the invention in the U.S. In the client's words, a grant is the USPTO's seal of approval that it has found no errors and the application provides enough evidence to protect the invention.

**Synonyms:** granted patent, issued patent

**Source:** USPTO website; client interview 2026-09-17

### Litigation Case

A lawsuit over a granted patent, typically for infringement, filed in a federal court. Litigation data is published separately from office action and grant data, and the client says it goes back about 21 years.

**Synonyms:** litigation data (the dataset as a whole)

**Source:** client interview 2026-09-17; `BR-litigation-history-window`

### Non-Final Office Action

An office action that rejects or objects to claims but leaves the applicant free to amend the claims and argue in response. It is the usual first office action an application receives.

**Synonyms:** non-final rejection, CTNF (see [Document Code](#document-code))

**Source:** USPTO website

### Office Action

An official letter from a USPTO examiner to a patent applicant explaining why the application cannot be granted as written. It lists the [Rejections](#rejection), cites the prior art or legal grounds behind them, and gives the applicant a deadline to respond with arguments or amendments.

**Office action data** means the dataset of these letters the USPTO publishes each week. In the 2026-10-18 sample, each record is one office action and includes the full letter text, the application number, art unit, Technology Center, examiner number, document code, filing and submission dates, and a list of rejections.

**Not to be confused with:** the application itself. The client described office action data as what happens "when you file a patent to protect your invention"; the office action is the examiner's response to that filing, not the filing.

**Source:** USPTO website; client interview 2026-09-17; 2026-10-18 sample weekly file

### Patent Application

A request to the USPTO to grant a patent for an invention, containing a description of the invention and the claims that define what is to be protected. It is identified by its [Application Number](#application-number).

**Source:** USPTO website

### Patent Family

The group of patent applications and patents that share a common original filing, for example a parent application and the continuation or divisional applications filed from it (its children). Tracing these parent and child relationships is called the patent's **lineage**.

**Synonyms:** lineage (the chain of parent and child applications within a family)

**Source:** client interview 2026-09-17; `BR-patent-lineage`

### Patent Prosecution

The back-and-forth between an applicant and the USPTO from filing until the application is granted or abandoned, including every office action and response.

**Not to be confused with:** prosecution in the criminal-law sense, or with [Litigation](#litigation-case), which happens after grant.

**Source:** USPTO website; `BR-separate-dataset-domains`

### Pendency

How long a patent application waits at the USPTO. The USPTO reports two forms: **first-action pendency**, from filing to the first office action, and **total pendency**, from filing to grant or abandonment.

**Note:** Which form the client wants for `BR-pendency-trend-metric` is still open. For scale, in the 2026-10-18 sample the median time from filing date to the office action's submission date was 805 days; this mixes first and later actions, so it is neither form above.

**Source:** USPTO website; `BR-pendency-trend-metric`

### Prior Art

Anything made public before an application's filing date (earlier patents, publications, products) that an examiner can cite to show an invention is not new or is obvious. It is the basis of §102 and §103 [Rejections](#rejection).

**Source:** USPTO website; client interview 2026-09-17

### Rejection

An examiner's finding, stated in an office action, that one or more claims cannot be granted, together with the section of patent law (35 U.S.C.) it rests on. The types the client named, plus one found in the sample data:

- **§101:** the claimed subject matter is not eligible for a patent (for example, an abstract idea).
- **§102:** the invention is not new, because a single piece of [Prior Art](#prior-art) already discloses it.
- **§103:** the invention is obvious in light of prior art, usually a combination of references.
- **§112:** the application does not describe or claim the invention clearly or completely enough, for example claims that are indefinite (§112(b)).
- **Double patenting:** the claims cover the same invention, or an obvious variation of it, as another patent or application by the same owner.

**Not to be confused with:** the client's shorthand "rejection codes", which refers to these legal sections, not to the USPTO's [Document Codes](#document-code).

**Note:** In the 2026-10-18 sample, each record's rejection list holds one rejection type, but the letter text often contains more. 2,087 records contain §102 rejection text without being tagged §102. Counts must say which source they use (`RI-Inconsistent-Source-Fields` in the vision and scope).

**Source:** client interview 2026-09-17; `BR-102-rejection`, `BR-103-rejection`, `BR-112-rejection`, `BR-double-patenting`; 2026-10-18 sample weekly file

### Technology Center

The USPTO's top-level grouping of examiners by broad field of technology, such as 1600 (biotechnology and organic chemistry) or 2100 (computer architecture and software). Each Technology Center contains several work groups and many art units.

**Synonyms:** TC (`techCenter` in the data)

**Source:** USPTO website; the 2026-10-18 sample covers 10 Technology Centers

### USPTO

United States Patent and Trademark Office, the federal agency that examines and grants patents and registers trademarks. It is the source of all data in this project and the subject of the client's posts.

**Source:** client project brief

### USPTO Open Data Portal

The USPTO's website for public data downloads and APIs, at https://data.uspto.gov. The weekly office action files come from here. API access requires a USPTO.gov account and API key, and the client reports occasional outages of about 2 minutes.

**Synonyms:** ODP

**Source:** client interview 2026-09-17; `DE-uspto-api`

### Visualization

A chart or overview the application produces from the imported data for one metric, such as office actions by rejection type and art unit. Each visualization is shown on its own tab, is linked to the records it was counted from, and can be exported as a labeled image for a post.

**Synonyms:** chart, visual

**Source:** `FEAT-Generate-Visualization` in the vision and scope; `UC-FEAT-create-visuals`, `UC-FEAT-export-visuals`

### Weekly Release

The set of files the USPTO publishes each week for bulk download, in particular the weekly office action file. The 2026-10-18 sample, `bdr_oa_bulkdata_weekly_2026-10-18.json`, is a single 383 MB file with one JSON record per office action, covering 8,667 office actions submitted 13–16 October 2026.

**Synonyms:** bulk data, weekly ZIP, weekly file. The client brief and interview describe ZIP files of 20–50 GB; the sample received is an unzipped JSON file. Which forms the application must accept is tracked under `AS-weekly-file-format` in the vision and scope.

**Source:** client interview 2026-09-17; `BR-weekly-uspto-publication`; 2026-10-18 sample weekly file

### Work Group

A subdivision of a [Technology Center](#technology-center) containing several related [Art Units](#art-unit), usually numbered by the first three digits of its art units followed by 0 (for example, 3780).

**Note:** The rule has exceptions: in the 2026-10-18 sample, 22 of 8,667 records have a work group that does not match their art unit's first three digits. The work group is therefore always taken from the data as given, never worked out from the art unit (SRS 7.2).

**Source:** `workGroup` in the 2026-10-18 sample weekly file
