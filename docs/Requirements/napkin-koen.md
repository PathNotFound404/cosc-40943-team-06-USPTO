# Napkin
 
## Shape
 
This is a local analytics platform that processes USPTO Office Action data and turns it into searchable insights, visualizations, and AI-assisted analysis. It is not a CRUD app and not real-time. It is primarily a batch data-processing and analytics system.
 
* Ingestion (ZIP files, bulk datasets, USPTO API)
* Parsing & indexing (Office Actions → structured records)
* Analytics engine (trends, examiner activity, Art Unit metrics)
* Local AI layer (summaries, Q&A, insight generation)
* Visualization & reporting (dashboards, charts, exports)
 
## The Hard Part
 
**Turning massive amounts of messy USPTO data into fast, reliable analytics on a user's local machine.** The challenge is not building charts or a desktop UI. The challenge is parsing large Office Action datasets, cleaning and organizing them, indexing them efficiently, and supporting analytics and AI queries without overwhelming CPU, memory, or storage. If this layer fails, every dashboard, report, and AI-generated insight becomes unreliable.
 
## Bottleneck
 
Two likely failure points:
 
* Under scale: parsing and indexing hundreds of thousands of Office Actions becomes slow, especially when new datasets require reprocessing large sections of the database. Poor indexing and retrieval performance will quickly make analytics and AI features unusable.
 
* Under a five-person team: integration between ingestion, analytics, AI, and UI components. Each subsystem can work independently while still failing when combined into a single desktop application.
 
## Stack
 
**Python backend + DuckDB + Ollama/llama.cpp + Tauri desktop UI.** Python provides strong libraries for document processing, analytics, machine learning, and local AI. DuckDB is designed for local analytical workloads and handles large aggregations efficiently. Ollama or llama.cpp supports local LLM execution, while Tauri provides a lightweight cross-platform desktop application.
 
## Kill Risks
 
* **Parser failure:** USPTO document formats vary across years and document types, causing extraction errors that silently corrupt analytics and charts.
 
* **Hardware limitations:** Local AI models consume too much RAM, CPU, or GPU resources, making the application slow or unusable on average consumer computers.
 
* **Unreliable anomaly detection:** Statistical outliers are presented as suspicious findings without sufficient evidence, causing users to lose trust in the system's conclusions.
 
## Verdict
 
Yes, but only with careful scope control.
 
Cut first:
 
* Advanced fraud detection
* Autonomous AI agents
* Complex hardware-aware model optimization
 
Focus on ingestion → parsing → indexing → analytics → dashboards → reporting. A desktop application that reliably processes USPTO datasets and generates
