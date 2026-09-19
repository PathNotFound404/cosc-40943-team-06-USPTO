# Client Interview Guide

**Project:** USPTO Patent Intelligence\
**Team:** 6\
**Client:** Malachi Hernandez, USPTO\
**Meeting:** #1

---

_**What this file is.** Your script going in, your meeting record coming out. Copy it once per meeting into `docs/requirements/` as `client-interview-YYYY-MM-DD.md` and commit it the same day._

_**How to use it.** Each section says what it is for, what it is worth in minutes, and whether it must happen in this meeting. The example questions are written for a different domain (technical recruiting) on purpose, so you cannot use them unchanged. Rewrite them in your client's words before you walk in, and write the answers underneath in **their** words rather than yours._

_**Work it with your agent.** Give it your one-page brief, this file **including these instructions**, and a role: "You are an experienced business analyst preparing for a first client interview. Using the question types in this guide, write the version of each question that fits this client's domain, and list every acronym in the brief you would want defined before the meeting." Then do the part it cannot: pick which of its questions are worth your client's limited hour. **Sort by what it costs you to stay wrong**, not by what is easy to ask. Anything you could answer by reading a document is not worth a client minute._

## Listen before you build

**An idea you propose in the first twenty minutes is not worth what it costs you.** Your strongest instinct will be to show your client you understood by describing what you would build. Early, that ends the elicitation: a client who has heard your idea reacts to it instead of describing their world.

This is about order, not silence. Some clients want to think out loud with you, and a few asked for the project because they want exactly that help. Do it **after** the read-back in section 14, when you can describe their process back to them accurately and the brainstorm is grounded in their world rather than your imagination. If they open by asking for your ideas, say you have some and would rather earn them by understanding the process first, then come back to it before you leave.

**The separate rule is absolute: commit to nothing.** Not a deadline, not a feature, not "sure, we can add that". Five teammates are not in the room. "Let me write that down and bring it back to the team" is the whole sentence, and it holds even when a client pushes.

## Before you go

- [ ] **Three roles assigned.** Lead asks and moves the agenda, one person not four. Scribe writes and does not ask, capturing exact words, especially nouns. Observer watches what is not said: hesitation, the topic they keep returning to, who they defer to.
- [ ] **Everyone has read the client's pitch slides** (TCU Online) and written questions individually before you merged them. The ones two of you wrote independently are the ones to ask.
- [ ] **Shortlist sent to the client the day before.** They arrive with answers instead of promises.
- [ ] **This file open on the scribe's laptop**, with someone on paper as backup.
- [ ] **Someone owns the clock.** You will not get through this guide, and that is expected.

## Meeting record

| | |
|---|---|
| **Date** | 2026-09-17 |
| **Time and location** | Remote on **Teams** |
| **Client participants** | **Malachi Hernandez**|
| **Team participants** | **Cody Pinkston:** Lead<br> **Bradley Helmholz:** Co-Lead<br> **Tanner Temple:** Scribe<br> **Turner Demott:** Owns Clock <br> **Edwin Rodriguez:** Observer <br> **Koen Dolezar:** Observer |
| **Recording** | Not Asked |
| **Photos of screens or forms** | Will receive soon |

_Ask to record, and say why: so nobody is transcribing instead of listening. If they decline, the scribe matters more. Ask separately about photographing screens, forms, and reports. A photo of the spreadsheet they actually use beats a page of notes about it._

## The shape of the hour

Most first meetings run 60 to 90 minutes. Budget for the short one.

| Part | Sections | 60 min | 90 min |
|---|---|---|---|
| Opening | 1 | 5 | 5 |
| The business | 2, 3 | 10 | 15 |
| The process | 4, 5, 6, 7, 8 | 25 | 40 |
| The boundaries | 9, 10, 11, 12 | 10 | 15 |
| The close | 13, 14, 15 | 10 | 15 |

**Extra time goes into section 4 first.** It repays another ten minutes and it is the only section you cannot reconstruct from notes afterward.

"Can wait" means the next meeting, not never. When you are behind, drop from the middle. **Never drop 14 or 15:** the read-back is where you learn you misunderstood something, and the close is where you stop losing two weeks to scheduling.

---

# Opening

## 1. Get to know your client

_**Must ask. 5 min.** Not small talk. Whose problem is this, how much of the domain lives only in this person's head, and how much of their own time do they have for you? A client fitting this around a full job answers email slowly, and you want to know that in week 3 rather than week 9._

_Tell me about your role and how it involves USPTO data or patent examination activity. How did you end up working with this kind of data? <br><br>What do you use it for today, and how much of your week does that take?_

**What they said:** Own business that relates to patents, IP/AI company he owns with a friend, 3 years old, company up for sale currently, products have matured
He also works in AI with small business, travels with US Department of state, is in a speakers program 6G, IP, his passion is IP
Goal for us to understand IP and provide data for others in a personalized setting (think Linkedin post). Sponsors TCU projects and Texas AM projects last 3 years, provides interesting senior projects.<br> This project is a space he wants to move into, has run dry runs to see what it takes to process the data, would take about 2-4 hours weekly to visualze the data and then another few hours to write the post, comes from several data sets (one is office action), other is weekly zips like application status, we can continue to talk about it as we go (comes from the UPSTO data site)
Takes 4-6 hours total a week to create this content on the data side, another 2-4 hours, so it takes 8 hours PER post
The **ONLY** person using this application is him, Malachi so that he can easily see them and copy them into his posts and website

---

# The business

## 2. Context and domain

_**Must ask. 5 min.** You are here for vocabulary as much as facts. Every term you do not recognize goes in the glossary before you leave. When your client says "cycle" in one sentence and "sprint" in the next, ask which they mean while they are still in front of you; an agent reading the transcript afterward cannot ask._

_Adapt: Give us some background on what you or your organization do with USPTO Office Action data, and why it matters to you?<br>_

**What they said:** These patent examiners read, look through database of patents and judge how the patent application is written based on the set of criteria to make sure it has the correct info in it. The USPTO publicizes these office actions with weekly zips, as well as API data which we can download when they publish the office actions. He prefers the bulk data bc the goal isn't to show individual patents, but a weekly overview of how the uspto is functioning, how well is this government agency functioning.<br>
These zip files usually are only a few gigabytes, weekly rollout (20-50 gb max in this zip file) → processing up to 100 gb a week in different chunks to get the data we need


**Terms for the glossary, in their words:** `Office Action Data:` when you file a patent to protect your invention.<br> 
`Art Unit:` group of people who go and review your patent, includes the patent examiner, subject matter expertise, looks at any prior knowledge before they file you a grant.<br> 
`A Grant:` seal of approval by USPTO that says they havent found any errors, we think your application provides enough evidence to protect your invention, then you get approved.
`Rejection Codes:` The office action comes in with rejections (102 or 103) that says there is an invention out there that is too similar to yours, or when your invention is too broad and doesnt have proper data (112 office action - double something rejection, two concepts that should be broken into different patents, need to be separated)

## 3. Business drivers and objectives

_**Must ask. 5 min.** Why this, why now. These become your business objectives, so push for a number: when they name a benefit, ask the follow-up nobody asks, **what is that number today?**_

_Expect to miss it here. Baselines surface in section 4, when they are looking at the thing that takes the time. Ask the objective now, listen for the number all hour, and close the gap in the read-back._

_Why did you propose this project — what problem or opportunity in USPTO data are you trying to address?<br> What is the most vital tool you are looking to get built if all the functionalities and features cannot be built in this timeframe?_

**What they said:** Several. Different data analytics, visualizations, EOD needs: 
Product non-negotiable needs to be built **doesnt hallucinate, doesnt break when it sees diff data. The data it pulls from, doesn't guess, makes concrete claims directly on the data.** Needs a paper trail to show where it pulls its conclusions from, needs a verification step. Most of this will be messy data processing and going to create clean images doesn't wanna use excel. Just open the laptop and see the visualizations. 


**Candidate objectives (`BO-<slug>`), with baselines where you got them:** _[Or "baseline unknown, `OI-*` raised".]_

---

# The process

## 4. How it works today

_**Must ask. 10 min, the best ten in the meeting.** Ask them to show you rather than tell you. People describe the process they believe they follow; the spreadsheet shows the one they actually follow, and the gap is where the requirements hide. **"Show me" is the two most productive words in requirements engineering, and they cost nothing.**_

_Walk one real recent case end to end. "Take me through the last one you did" beats "how does it usually work", because the general shape is a summary they have given before and the last real one has the exceptions in it._

_Walk me through the last time you actually analyzed a batch of Office Action data, start to finish. What format did it come in, where did you get it, and what did you do with it step by step?_

**What they said:** MAY THIS WEEKEND SHOW UP HOW IT WORKS THIS WEEKEND AND HIS THOUGHT PROCESS
Then write questions based on this


**Artifacts they showed us:** Nothing as of yet, client states they will send video and data this weekend.

## 5. What is hard about it

_**Must ask. 5 min.** The complaint is usually the requirement. Listen for "must", "unless", "only", and "except", which arrive unannounced in the middle of a story about something else. Those sentences are business rules, and they exist whether or not your software does._

_What's the most frustrating part of working with this data today?_

**What they said:** Hates the data gov puts out, not cleaned in any sense, is just a dump of data they give. Sometimes the dump is siloed, have Office action zip, litigation zip, etc. means they have different application numbers across these areas but not easy to see the different paths between the data sets.<br>
Wants a system that understand this a bit easier, understands grant numbers, litigation numbers etc. Gives associations based on the data sets


**Rules heard (candidate `BR-*` for week 4):** _[Write each as their policy, not as software behavior.]_ Associate files based on litigation number or grant number 

## 6. What already works

_**Must ask. 3 min.** Ask what is good before you propose replacing it. A team that removes something the client liked has lost trust it will not get back this semester, and nobody volunteers this unasked._

_What would you keep exactly as-is from your current process or tools?_

**What they said:** There is curently on tool for this and this is not even a process that he currently does by hand. He knows CS from system side not the execution side(Actual Code).
Asking us to put together the best way to link this data together, want our team to design the data analysis process (no process exist currently) and then build the app


## 7. Volumes and scale

_**Must ask. 3 min.** These numbers decide most of your architecture, and they are cheap to ask for and expensive to guess. Twenty records a semester and two hundred thousand a day are different systems._

_How many Office Actions do you typically process — per week, per month, per year?<br>How far back does historical data need to go?<br>What hardware do your intended users actually have — typical RAM, whether they have a discrete GPU — since local AI model performance depends on it?_

**What they said:** Analyse the USPTO zip about once week.<br>base requirement
Monthly to yearly overview would be nice but not necessary at this moment.<br> Monthly and yearly, also litigation area which happens after filed grant (which goes back 21 years).<br>As of now, has a `macbook air 24 gb ram, 2tb ssd, 2022, 10 core 10 core 8 core`
Would be NICE to switch to windows, but also don’t see himself downgrading neither upgrading specifically. 
Either online in low to no cost function, or app that he can launch for only him.


## 8. Who the users are

_**Must ask. 4 min.** The person who commissions software is often not the person who uses it._

_**If you cannot reach the real users, that is a project risk, not a scheduling detail.** Record it as an `RI-<slug>` the same day. Building from a proxy's account is the most common way a capstone ships something nobody uses, and it is survivable only if you know you are doing it._

_Who would actually open this application day to day?_

**What they said:** This application is a passion project just for him to use.

**Can we reach real users? If not, why, and what is the risk:** Yes we can reach the user as it is just him. 

---

# The boundaries

## 9. Constraints and rules

_**Must ask. 4 min.** Nobody asks these in meeting 1 and everybody regrets it in November. A constraint restricts how you may build, and it is a requirement even though it describes no behavior. Ask directly; clients do not volunteer these, they assume you know._

_Is there anything we're required to use or forbidden from using — a specific database, a specific AI model family, an approved-software list?<br>Any hard deadlines we haven't been told about? Is there a budget for anything (model files, storage, licenses), and who signs off?_

**What they said:** Not necessarily any restrictions, wants as cheap as possible. Preferably no connections to openai anthropic etc, he wants cheap automated process, not supervised, does NOT need to be quick.<br>
Again, its part of his personal brand, bankrolling AI is going to get wild as it does so low cost.<br>
USPTO data by december, not a hard deadline, just what he thinks based on past semesters.
Then in spring to look at european data, chinese data maybe.


## 10. External dependencies

_**Must ask. 3 min.** What your system has to talk to. Access credentials take weeks to obtain, so the ask has to happen now._

_Beyond the USPTO's own weekly Office Action ZIP files and bulk datasets — does this need to talk to any other system: an internal database, a document management system, a reporting tool you already use?<br>If we use the USPTO API instead of file downloads, who holds the credentials, and what are the rate limits or terms of use?_

**What they said:** Just the zips and bulk data sets<br>Rate limits on USPTO api’s we rarely hit them, for active pulls the limits are kind of in the dark, depends on who uses it, sometimes just randomly drops for 2 minutes, usually pulling data every minute/90 seconds.
For bulk data sets, you dont need ongoing data pulls, its just one time.


## 11. Lifetime and who maintains it

_**Must ask. 2 min.** The question students never ask and every client can answer. **Who runs this after we graduate, and what do they already know how to run?** It constrains your entire technology choice, so ask before you pick a stack rather than after._

_How long should this keep running? Who supports it after we graduate from TCU? What do they already maintain, in what languages? Who pays for hosting next year, and who owns the accounts?_

**What they said:** It is just him and he does not currently maintain any projects.

## 12. Other stakeholders

_**If there is time. 1 min.** Cheap, and occasionally it turns out somebody with a veto has not been consulted._

_Who else could be affected by this — legal/compliance, IT/security (given it touches USPTO data and runs local models), other analysts who'd want access?_

**What they said:** No other stake holder since the project is just for him.

---

# The close

## 13. Anything else

_**Must ask. 1 min.** Ask it, then stop talking and wait through the silence. Highest-yield question in the guide, and it only works if you do not fill the pause._

_Is there anything I should have asked and did not? What have we not talked about that worries you?_

**What they said:** Could not think of anything thinks we covered it all.

## 14. The read-back

_**Never skip. 5 min.** The part teams cut when they run late, and the highest-value five minutes of the hour. Say what you understood in your own words and watch for the correction. A client who is nodding may be being polite; a client correcting you is engaged, and that correction is usually the single most useful sentence of the meeting._

_Read back four things: the problem in one sentence, the objectives with any numbers you got, the top three things you heard are hard, and one thing you believe is **out** of scope. The last produces more correction than the other three together._

_Fill in the [vision-and-scope.md](vision-and-scope.md) vision statement table during the meeting, read its six rows aloud, and see what they fix. Ninety seconds._

**What we read back, and what they corrected:** The problem is that USPTO data is messy to analyse and there currently does not exist an apps to do this. The biggest objective is to organize and analyse the messy data. The next being including AI analysis that is based on concrete evidence and does not hallucinate. The cross platform functionality of the app seems to be out of scope as this will only be running on one Mac book. There were no corrections.

## 15. Before you leave the room

_**Never skip. 4 min.** Unglamorous, and where teams lose two weeks._

- [ ] **Next meeting on the calendar** before anyone stands up. Not "we will be in touch". `Thursdays at 7pm, weekly on teams.`
- [ ] **Cadence agreed:** how often, roughly how long, and in person or remote. This course expects meetings **in person, on campus** where your client can travel; if they are outside DFW, agree the tool and who sends the link. `Cadence: Weekly now, may shift to bi-weekly`
- [ ] **Contact channel and how fast they reply.** `Email,states he will respond within 24 hours`
- [ ] **Who to contact between meetings**, including when this person is away. `Malachi is the only contact`
- [ ] **Copies requested** of every artifact you were shown. `Malachi will send a video this week and link to the data`
- [ ] **Introductions requested** to anyone named in sections 8 and 12. Who: `No one just malachi`
- [ ] **Say what happens next**, in one sentence, so they know what to expect and when.

---

# After the meeting

_File everything within 24 hours, while you still remember why each answer mattered. This file is a record, not a home._

| Section | Feeds |
|---|---|
| 1, 2 | [project-glossary.md](project-glossary.md), and Background in [vision-and-scope.md](vision-and-scope.md) |
| 3 | Business Opportunity, Objectives, and Success Metrics in [vision-and-scope.md](vision-and-scope.md) |
| 4, 6 | Background and the process flow in [vision-and-scope.md](vision-and-scope.md); use cases in week 4 |
| 5 | Business rules catalog, week 4 |
| 7, 9, 10 | Quality attributes, constraints, and external interfaces in the specification, week 4 |
| 8, 12 | Stakeholder Profiles in [vision-and-scope.md](vision-and-scope.md) |
| 8, 11 | Risks (`RI-<slug>`) and assumptions (`AS-<slug>`) in [vision-and-scope.md](vision-and-scope.md) |
| 14 | Scope and the vision statement in [vision-and-scope.md](vision-and-scope.md) |
| Anything unanswered | [OPEN-ISSUES.md](OPEN-ISSUES.md) |

## Initial ideas

_[Solutions anyone floated, yours or theirs. Record them here and nowhere else yet. A solution the client already picked ("then I select the state from a drop-down") is not a requirement, and writing it into the specification makes a design decision on their behalf. Ask why until you reach the need underneath, then write down the need.]_

## Disagreements and hesitations

_[The observer's section, and the one that evaporates fastest. Two participants using the same word differently. A question answered by the wrong person. A topic they returned to three times. An answer that changed between the start and the end. A visible pause before "yes". None of it is evidence on its own; all of it tells you where to look next.]_

## Open questions

_[Everything you could not answer, and everything they answered with "I would have to check". Copy each into [OPEN-ISSUES.md](OPEN-ISSUES.md) as an `OI-*` with the person who can answer it, then sort them before the next meeting by what it costs you to stay wrong.]_

---

_**Within 24 hours**, send the client your notes and the open questions. It creates the record and gives them a second chance to correct you while the meeting is fresh. Then commit this file._
