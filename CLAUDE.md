# CLAUDE.md — OpenEMR RAG Project Guide

This file provides guidance for AI assistants working on the OpenEMR-RAG codebase.

---

## Project Overview

OpenEMR-RAG is an **educational proof-of-concept** that integrates Retrieval-Augmented Generation (RAG) with OpenEMR (an open-source Electronic Medical Record system) to provide AI-powered clinical decision support. All LLM inference runs **locally** via Ollama — no patient data is sent to external APIs.

**Primary use case:** A clinician selects a patient, then asks natural-language questions; the system retrieves relevant clinical guidelines from a local vector store and combines them with the patient's chart data to generate contextualized answers.

---

## Repository Structure

```
openemr-rag/
├── openemr_rag.py              # Main CLI application (RAG core + interactive REPL)
├── openemr_cds_server.py       # Flask REST API server (port 3005)
├── app/
│   └── app.py                  # Streamlit web UI (future / optional)
├── knowledge_base/
│   └── clinical_guidelines/
│       ├── sample_guidelines.txt   # Drug interactions, BP & diabetes guidelines
│       └── clinical_reference.txt  # JNC 8, ADA, vital-sign reference ranges
├── index.html                  # Standalone browser UI (no build step required)
├── requirements.txt            # Python dependencies
├── setup.bat                   # Windows setup & validation script
├── start_server.bat            # Launches Flask REST API (Windows)
├── Run-RAG-Interactive.bat     # Launches CLI (Windows)
├── README.md                   # User-facing documentation
├── LOVABLE_SPEC.md             # UI/UX specification for Lovable-based frontend
└── CONTRIBUTING.md             # Contribution guidelines
```

---

## Entry Points

| Interface      | File                     | How to Run                                   |
|----------------|--------------------------|----------------------------------------------|
| Interactive CLI | `openemr_rag.py`        | `python openemr_rag.py`                      |
| REST API       | `openemr_cds_server.py`  | `python openemr_cds_server.py`               |
| Streamlit UI   | `app/app.py`             | `streamlit run app/app.py`                   |
| HTML UI        | `index.html`             | Open directly in a browser                   |
| Windows CLI    | `Run-RAG-Interactive.bat`| Double-click or run from cmd                 |
| Windows server | `start_server.bat`       | Double-click or run from cmd                 |

---

## Architecture

### RAG Pipeline

```
knowledge_base/*.txt
      ↓
RecursiveCharacterTextSplitter (chunk=1000, overlap=100)
      ↓
OllamaEmbeddings ("nomic-embed-text", localhost:11434)
      ↓
FAISS vector store  →  persisted at vector_store/faiss_index/
      ↓  (similarity search, k=4)
ChatPromptTemplate  ←  patient summary injected here
      ↓
OllamaLLM ("alibayram/medgemma:4b", temp=0.3)
      ↓
Clinical response
```

### Key Classes

**`openemr_rag.py`**
- `Colors` — Terminal ANSI color helpers for CLI output.
- `OpenEMRAPI` — REST client + SSH tunnel manager for the remote OpenEMR instance.
  - `start_ssh_tunnel()` / `stop_ssh_tunnel()` — manages local port-forwarding.
  - `get_patient_data(pid)` / `get_patient_summary(pid)` — fetches chart data.
- `OpenEMRRAG` — Orchestrates the LangChain RAG pipeline.
  - `ingest_knowledge_base()` — builds and persists the FAISS index.
  - `load_existing_vectorstore()` — loads the persisted index on subsequent runs.
  - `setup_qa_chain()` — wires retriever → prompt → LLM.
  - `query(question, patient_context)` — runs a RAG query.
  - `interactive_mode()` — REPL command loop.

**`openemr_cds_server.py`**
- Flask app exposing the RAG system over HTTP.
- Lazy-loads `OpenEMRRAG` on first API call.
- Includes hardcoded **demo patients** (Sarah Johnson, Michael Chen, Emily Rodriguez) for offline testing.
- CORS enabled for all origins.

### REST API Endpoints (port 3005)

| Method | Path                    | Description                              |
|--------|-------------------------|------------------------------------------|
| GET    | `/health`               | Service health check                     |
| GET    | `/debug`                | Connectivity debug info                  |
| POST   | `/connect`              | Start SSH tunnel to remote OpenEMR       |
| POST   | `/disconnect`           | Stop SSH tunnel                          |
| GET    | `/patient/<id>`         | Get patient data (`?mode=demo\|live`)    |
| GET    | `/patients`             | List/search patients (`?mode=...&search=...`) |
| POST   | `/query`                | Clinical RAG query with patient context  |
| POST   | `/analyze/<type>`       | Specific analysis (vitals/medications/risks/gaps) |

---

## Dependencies

Install with:
```bash
pip install -r requirements.txt
```

Key packages:

| Package | Role |
|---------|------|
| `langchain` / `langchain-community` / `langchain-ollama` | RAG orchestration |
| `langchain-text-splitters` | Document chunking |
| `faiss-cpu` | Local vector database |
| `flask` + `flask-cors` | REST API server |
| `requests` | HTTP client for OpenEMR API |
| `streamlit` *(optional, commented out)* | Web UI |

**External runtime requirement:** [Ollama](https://ollama.ai) must be running locally on port 11434 with:
- `ollama pull alibayram/medgemma:4b` — LLM for clinical reasoning
- `ollama pull nomic-embed-text` — embedding model for vector search

---

## Hardcoded Configuration (known tech debt)

The following values are currently hardcoded and should be moved to environment variables before any production-like use:

| Value | Location | Description |
|-------|----------|-------------|
| `16.58.52.89` | `openemr_rag.py` | AWS EC2 OpenEMR host IP |
| `C:\\Users\\leobe\\.ssh\\OpenEMRLeo.pem` | `openemr_rag.py` | SSH private key path (Windows-specific) |
| `3001` | `openemr_rag.py` | Remote OpenEMR API port |
| `3005` | `openemr_cds_server.py` | Flask server port |
| `localhost:11434` | both files | Ollama endpoint |
| `alibayram/medgemma:4b` | both files | LLM model name |
| `nomic-embed-text` | both files | Embedding model name |
| `vector_store/faiss_index` | both files | Vector store path |

When modifying configuration, update **both** `openemr_rag.py` and `openemr_cds_server.py`.

---

## Development Workflows

### First-time setup
```bash
# 1. Create and activate virtual environment
python -m venv venv
source venv/bin/activate   # Linux/Mac
venv\Scripts\activate      # Windows

# 2. Install dependencies
pip install -r requirements.txt

# 3. Pull required Ollama models
ollama pull alibayram/medgemma:4b
ollama pull nomic-embed-text

# 4. Build the vector store (one-time)
python openemr_rag.py   # selects "Ingest" on first run if no index exists
```

### Adding clinical guidelines
1. Drop `.txt` files into `knowledge_base/clinical_guidelines/`.
2. Re-run ingestion: delete `vector_store/faiss_index/` then restart the CLI or call `POST /query` (which triggers lazy rebuild).

### Running the API server
```bash
python openemr_cds_server.py
# Server starts on http://localhost:3005
# Demo mode works without any OpenEMR connection
```

### Interactive CLI commands
```
ask <question>         — RAG query with current patient context
patient <id>           — Load a patient by ID
analyze <type>         — Run analysis (vitals/medications/risks/gaps)
history                — Show query history
<plain text>           — Treated as an implicit "ask" query
```

---

## Code Conventions

- **Style:** PEP 8. No formatter (black/ruff) is configured yet.
- **Type hints:** Used selectively; not enforced by tooling.
- **Logging:** Uses `print()` with `Colors.*` helpers for CLI; Flask default logger for server.
- **Error handling:** Try/except blocks with descriptive messages; falls back to demo data when the live OpenEMR connection fails.
- **No tests:** The project has no automated test suite. Manual validation is done by running the CLI or checking the `/health` endpoint.

---

## Security & Privacy Notes

- **PHI handling:** Patient data is held **in memory only** during a session. Nothing is written to disk.
- **Local inference:** Ollama runs entirely on the local machine; no data leaves the host.
- **SSH tunnel:** Communication with the remote OpenEMR instance is encrypted via SSH port-forwarding.
- **Demo mode:** The Flask server defaults to demo mode with synthetic patients — safe for development.
- **Do not commit:** SSH keys, `.pem` files, `.env` files, real patient data, or `vector_store/` directory contents.

---

## File Ignore Patterns

`.gitignore` excludes: `__pycache__/`, `*.pyc`, `venv/`, `*.pem`, `*.gguf`, `*.bin`, `vector_store/`, `*.log`, IDE directories.

---

## Known Limitations & Areas for Improvement

1. **No test suite** — add pytest with unit tests for `OpenEMRRAG.query()` and API endpoints.
2. **Hardcoded config** — move to `.env` / environment variables.
3. **Windows-only startup scripts** — add Linux/Mac equivalents.
4. **SSH cleanup** uses `taskkill` (Windows-specific) — needs cross-platform fix.
5. **No linter/formatter** configured — consider adding `ruff` or `black`.
6. **No CI/CD** — no GitHub Actions workflows exist.
7. **In-memory query history** — lost on restart; could be persisted if needed.
8. **Single-user design** — Flask server has no auth; not suitable for multi-user deployment.

---

## Branch & Git Conventions

- Work on feature branches following the pattern `claude/<description>-<id>`.
- Commit messages use `Add:`, `Fix:`, `Change:`, `Remove:` prefixes (see git log).
- Main production branch is `master`; `main` is the remote default.
