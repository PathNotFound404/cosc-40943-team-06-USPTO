# AI Assistant Design

**Project:** USPTO Patent Intelligence
**Team:** 06
**Area:** `UC-FEAT-*`, local AI assistant (`FEAT-Query-AI`). Every use case shares the area code `FEAT` ([use-cases.md](../requirements/use-cases.md) section 3), so the design documents are split by feature area, as [architecture 5.2](architectural-design.md#52-use-case-areas-and-components) does.

> **Realizes:** nothing yet. `UC-FEAT-query-ai` and `FR-VERIFY-ai-claims` are **deferred**.
> **Depends on:** `KD-no-ai-in-mvp`
> **See:** [use cases](../requirements/use-cases.md), [architecture-of-record](architectural-design.md) (5.2, 9.2), [verification design](verification.md)
> **Designed against:** not designed.

---

## Deferred

Release 1.0 has no AI features (`KD-no-ai-in-mvp`; vision and scope 4.3 lists `FEAT-Query-AI` as a stretch feature). This area is **not designed**, on purpose. A design written now would have to guess the runtime, the model, and its licence (`CO-open-weight-models`, `CO-model-licensing`, `SI-local-ai-runtime`), none of which has been chosen, and an agent reading a guessed design would build it.

What a future design must start from, all already recorded elsewhere:

- The AI Assistant component answers only from records Provenance returns ([architecture 5.2](architectural-design.md#52-use-case-areas-and-components), `KD-no-ai-in-mvp` trade-off), so it reuses `provenance.records_for` from the [verification design](verification.md).
- `FR-VERIFY-ai-claims`, `SAF-ai-grounding`, `PER-ai-response`, `ROB-low-resources`, and `MNT-model-swap` become its acceptance criteria.
- It adds the first second process (the local runtime) and the first network-adjacent interface (`SEC-local-services`), so it will change the architecture-of-record.

When `FEAT-Query-AI` comes into scope, run `/design UC-FEAT-query-ai` and it will replace this page with a full design from the [template](design-of-record.md).
