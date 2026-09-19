# Napkin

## Shape
This is a local data pipeline with an embedded analytics/ML layer, wrapped in a desktop UI not a CRUD app (no meaningful create/update from users, it's ingest-and-read) and not real-time (batch ingestion, async processing).

* Ingestion (ZIP/XML/API → parsed records)
* Storage/Index (SQLite/DuckDB + a search/vector index)
* Analytics engine (aggregation, trend, anomaly detection)
* Local AI layer (LLM inference for summarization/Q&A)
* Visualization/export (charts, reports)

## The Hard Part
**Packaging a local AI + data-processing stack so it runs reliably, without a network fallback, on an arbitrary unknown consumer machine.** It's not the analytics logic (that's normal data engineering) and not the UI — it's making llama.cpp/Ollama-class inference, a search index, and a processing pipeline auto-detect hardware, scale down gracefully, and install as one double-clickable app on both macOS and Windows with zero manual setup. That's a systems/DevOps problem disguised as a feature bullet, and it's usually the thing that eats a team's entire semester.

## BottleNeck 
Two different failure points:

* Under scale: ingestion/parsing throughput once "large volumes of USPTO Office Action data" means hundreds of thousands of documents — naive parsing will choke, and re-indexing on every update will make the app unusable.

* Under a five-person team: the seams between the data pipeline, the analytics engine, and the local AI layer. Nobody "owns" the interface contracts between them, so integration happens in week 12, the packaging step (bundling three different runtimes into one installer) is the last thing anyone touches, and it's the first thing that breaks.

## Stack    
**Python for the whole backend (pandas/DuckDB for analytics, Ollama or llama.cpp bindings for inference) + SQLite/DuckDB for storage + a thin Electron or Tauri shell for UI.** Reason: one language across ingestion/analytics/AI minimizes cross-language integration risk (the actual hard part above), and every piece here has mature libraries and huge Stack Overflow coverage — a student team on a deadline should not be debugging a custom Rust FFI layer to llama.cpp when Python bindings already exist. Tauri over Electron only if someone on the team already knows Rust; otherwise Electron is the boring, safer default despite being heavier.

## Kill Risks 
* **Installer rot:** a one-click cross-platform installer that bundles a local LLM runtime silently fails on machines with insufficient RAM/no GPU/locked-down permissions, and the team discovers this in week 14 during the demo, not before.

* **Format drift:** USPTO Office Action ZIP/XML schemas are inconsistent across years and doc types, so the parser silently mis-extracts or drops records instead of crashing — corrupting every downstream chart without anyone noticing until numbers look wrong.

* **Unfalsifiable anomaly claims:** "fraud/anomaly detection" ships as a headline feature with no labeled ground truth to validate against, so it either flags too much (noise, no credibility) or too little (looks broken), and there's no way to demonstrate it's actually working rather than pattern-matching noise.

## Verdict
No, not as scoped, for a typical semester team of five. Feasible if cut hard.

Cut first: local LLM Q&A and the fraud/anomaly-detection layer — both are research-grade problems being treated as checklist items. Ship a real, working pipeline that does ingestion → parsing → indexing → Art Unit/examiner/trend analytics → dashboards/export, running well on one OS first (pick macOS or Windows, add the other only if time remains). That alone is a legitimate, demoable data-engineering project; the AI/anomaly layer is what turns it into a science-fair promise that collapses under a five-person team's actual hours.
