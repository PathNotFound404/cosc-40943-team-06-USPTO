---
description: Build one use case from its merged design-of-record. plan, a refactor proposed first if one is needed, trunk then leaves, the design's test list, and a pull request. Run /design first.
argument-hint: <UC-ID>  (for example /implement UC-ORD-place-order)
---

# /implement: build a use case from its design

Take the use case named in `$ARGUMENTS` (for example `UC-ORD-place-order`) from its **design-of-record** to working, tested code in a pull request. This is the second of two build stages. The use case is the contract, its business rules and cited `FR-*` are the acceptance criteria, the glossary fixes the vocabulary, and **the design is how you build it**.

**Precondition: a merged design.** Confirm `docs/design/<area>.md` is on `main` and covers this use case: its *Realizes* line lists the `UC-*`, and its row in `docs/traceability.md` reads `📐 Designed`. **If there is no merged design, stop and tell the developer to run `/design <UC-ID>` first.** Do not design inside the build.

**Precondition: a fresh session.** The build reads the merged design, not the conversation that produced it. If this session already holds the `/design` conversation or unrelated work, ask the developer to run `/clear` and start again. Anything the documents do not answer is a gap in the design: ask, then fix `docs/design/<area>.md` on this branch and name the change under Reviewer focus.

**The specification and the design are authoritative, not infallible. Challenge them.** When a step is ambiguous, a decision contradicts the code or the specification, or a constraint looks stale, **ask or push back. Do not silently comply and do not invent the missing detail.** Propose the specification edit, or update the design. Saying a better way exists is not building it: an improvement the use case does not need is proposed, never made unasked.

If no UC-ID is given, ask which use case to build, or list the rows in `docs/traceability.md` whose **Build** is `📐 Designed`, earliest **Release** first.

The design was approved at its pull request, so there is no second approval of the design. **You stop in two places:** before any code, if the use case needs a refactor the design does not name; and after the trunk commit, so the developer reads the shared code before the leaves are built on it. Stop as well whenever the documents contradict each other or leave a decision open.

## Phase 1: understand the design and the specification (read only)

1. **The design-of-record**, `docs/design/<area>.md`: the sequence diagrams, components, API contract, key decisions, data model, and the **test list**. This is what you build.
2. **The use case** in `docs/requirements/use-cases.md`, found by its identifier: the main success scenario and **every extension**. These are the flows your tests cover.
3. **Its business rules** (`docs/requirements/business-rules.md`) and any `FR-*` or quality attribute in `docs/requirements/software-requirements-specification.md` it depends on. Confirm every cited identifier exists.
4. **The vocabulary** in `docs/requirements/project-glossary.md`. Use its terms in identifiers and UI text.
5. **The architecture-of-record**, `docs/design/architectural-design.md`: the containers and this area's component, and **section 8 (Crosscutting Concepts) in full**, 8.1 Security and every 8.2 rule (error handling, time, and the rest). Where existing code breaks a convention, follow the convention, not the code, and note the drift for the pull request.
6. **The team's charter** (`CLAUDE.md` or `AGENTS.md`), including the list of things the agent must not do. Two of them hold everywhere: **no dependency is added until a person confirms it exists and is the one we meant**, and never remove the `Co-Authored-By` trailer from a commit.
7. **The row** in `docs/traceability.md`, and **the existing code** the design points at.

**If the design disagrees with the specification or the code, say so now,** before building on the contradiction.

## Phase 2: plan, then go on (no approval gate, except for a refactor)

State a short plan and go on to Phase 3 without waiting:

- **Acceptance criteria**: the main flow and every extension, as testable outcomes.
- **Back end and front end changes**, realizing the design's components and API contract, including who may call each endpoint and how that is enforced.
- **Tests**: every row of the design's test list, mapped to the code that will make it pass. An extension with no test is an untested requirement.
- **Where the plan departs from the design**, if anywhere. A departure updates the design in Phase 3.
- **The trunk**: which commits are shared code (code many flows depend on, code that changes behavior existing users rely on, or code that is hard to roll back), and which are leaves.
- **Open questions and risks.** A real blocker stops you here.

## Phase 3: build

Work on a branch, never on `main`, and **commit in steps a reviewer can read, cut along the design.**

- **A refactor the use case needs is proposed before it is made.** If the existing code must change shape first (a method extracted, a class split, logic moved to one owner), stop before writing any code. Tell the developer what you would change, why the use case needs it, and every place the old way appears. Make it only after they agree, in a commit of its own, first: no behavior change, the existing tests green before and after, finished everywhere the old way appears. A refactor the design already names needs no second approval.
- **Trunk next, in a commit of its own.** Then **stop**: tell the developer which commit to read, and ask them to say what it changed and why. Continue when they can.
- **Then one commit per leaf**: each flow's own endpoint, view, or job.
- **A security rule or a schema migration goes in a commit of its own,** so the reviewer sees it alone.
- **Each commit carries the tests for what it adds** and passes them, run as targeted tests, not the full suite.
- **A small use case with no trunk** is one commit and no pause, except that a security rule or migration still goes alone.

Inside each commit, follow the project's conventions and the design. Keep the change to this use case: a rename, a tidier method, or a convention fixed elsewhere is listed under Reviewer focus as a follow-up, not made. **Keep the design honest:** if the build forced a change from the design, update `docs/design/<area>.md` to describe what was built.

## Phase 4: test and verify

1. **Every row of the design's test list has a test,** the main flow and every extension. A test asserts what the use case and its rules require (its oracle), not what the code happens to return.
2. **Check the diff against section 8 before running anything.** For each 8.2 rule, confirm the new code follows it (for example: errors in the shape 8.2 fixes, calendar time from the injected clock, the caller's identity from the session and never the request body). For 8.1, confirm every new endpoint has its access rule and a test for each refusal. Fix a miss, or record it as a deliberate departure.
3. **Run the full test suites** once every commit is in, and make them pass. If they take long, the developer may run them; report the result either way.
4. **Run the feature** where practical and confirm the main success scenario behaves as the use case says.
5. **Report faithfully** what passed, what was skipped, and why.

## Phase 5: trace it back

Update the row in `docs/traceability.md`: **Build** to `🟡 In progress` or `✅ Built`, and **Verify** from the tests that exist (`✅ Verified` only if they cover the main flow and every extension and pass; `🟡 Partial`, naming the gap in the Tests cell; `🔎 None` if nothing tests it). Fill Code and Tests, noting which extensions each test covers. Built but untested reads `✅ Built` and `🔎 None`; that honesty is the point.

If the build showed the use case or a rule to be wrong or incomplete, say so and propose the specification edit.

## Phase 6: open the pull request

Keep the commits separate. Draft the description from `.github/PULL_REQUEST_TEMPLATE.md`, at most three lines per section:

- **Traces to:** the use case and `docs/design/<area>.md`.
- **How it was verified:** under Verified, each test-list row and the test that covers it, and what Phase 4 ran. Under Not verified, every extension the row marks untested and anything skipped. Never state a confidence level.
- **Reviewer focus:** which commit is the trunk, any refactor commit and why the use case needed it, every change to shared code (a new access rule first), and any change to the design, named as a design change.

Recommend a fresh-context review (a new session, or `/code-review`) before a human reviewer, with its findings added under How it was verified. Then tell the developer the pull request is ready for **a teammate who did not write it**, and that once it merges they close the use case (the [method](https://washingtonwei.github.io/cosc-40943/method/), Phase C) before starting the next.
