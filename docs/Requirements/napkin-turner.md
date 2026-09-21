# Napkin — Turner

Individual silent-work pass (~5 min) on the "Local Patent Intelligence & USPTO Operations
Analytics" project, following the six-prompt napkin method.

## 1. Shape

A local-first data pipeline and analytics/ML application with a desktop UI on top.

```
[Drag-drop ZIP / API] -> [Ingest & Parse] -> [Local DB/Index (SQLite/DuckDB)]
        -> [Analytics Engine] -> [Local LLM] -> [Dashboards / Export]
```

## 2. The hard part

Running ingestion, indexing, statistical analysis, and LLM inference entirely on the
user's machine, with zero cloud calls, while staying responsive on unknown consumer
hardware. The data engineering (parsing/cleaning USPTO Office Action data) is tedious but
well-understood; the differentiator is making local AI and anomaly detection usable
without a GPU cluster.

## 3. Bottleneck

Two likely failure points:
- **Ingestion at scale:** weekly bulk ZIPs are large. Naive single-threaded parsing and
  indexing will choke before "processing potentially very large collections" is satisfied.
- **Local LLM inference under resource constraints:** low-RAM/no-GPU machines will be slow
  or unable to run the AI-assisted insights features unless the app detects hardware and
  scales model size/usage accordingly.

Team coordination risk is secondary but real: data pipeline, analytics, AI, and UI need to
be separated cleanly enough that 4+ people can build them in parallel without blocking.

## 4. Stack

- **Backend/processing:** Python. Richest ecosystem for data parsing, stats, and AI
  runtime bindings, and the team likely already knows it. Rust/Go would be faster but
  slower to build with on a course-length project.
- **Local storage/analytics:** DuckDB. Fast columnar analytics on local files with no
  server to manage, fits the "no manual DB configuration" requirement.
- **UI framework:** Electron or Tauri. Cross-platform macOS/Windows requirement rules out
  native-per-OS; Tauri is lighter-weight if the team wants a smaller bundle and is willing
  to pair a Rust shell with a web frontend.
- **Local inference:** llama.cpp or an Ollama-style runtime. Supports swappable
  open-weight models and scales quantization to available hardware.
- **Search/vector index:** a lightweight embedded vector store (e.g. FAISS/Chroma) for
  document retrieval feeding the LLM.

Default to boring, well-documented tools everywhere except the two "hard part" pieces
(local inference, anomaly detection), where the actual project value lives.

## 5. Kill risks

1. **Local LLM doesn't run acceptably on a typical grading/demo machine** (no GPU,
   8-16GB RAM). The AI-assisted insights feature becomes unusable or gets faked with a
   tiny model that gives bad answers.
2. **Dependency bundling failure.** Python env, AI runtime, and DB don't actually
   auto-launch cross-platform, so "the user does not need to manually configure" breaks
   and the app fails to run out-of-the-box on a teammate's or grader's machine.
3. **USPTO data format churn.** Office Action ZIP/XML structure varies enough across
   years that the parser silently drops or mis-classifies records, corrupting every
   downstream analytic (Art Unit stats, anomaly flags) without an obvious error.

## 6. Verdict

**Feasible for this team/timeline, with scope cuts.** Full anomaly/fraud detection,
multi-model swapping, and polished export/reporting are stretch goals, not MVP. First cuts
if time runs short: drop AI-assisted natural-language Q&A first (keep only
summarization), then drop live model-swapping (ship with one fixed small local model),
then drop publication-grade export styling (keep functional charts). Core, non-cuttable
path: ingest, parse, store, and an Art Unit/examiner analytics dashboard. That's the
minimum that proves the data can be processed and turned into clear information.
