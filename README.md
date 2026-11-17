# OrganizerAI 🗓️

> **Messy event brief in → Executable plan out.**
> An agentic copilot for Indian event organizers — structured output, predictive ML, and a human approval gate before any risky action.

---

## Architecture

```
Next.js UI  ──REST──►  FastAPI  ──►  LangGraph planner
                           │               │
                           │        Gemini / Ollama
                           │               │
                        SQLite          interrupt()
                       /ChromaDB     Approval queue
                       /FAISS          │
                           │        resume → execute
                      RAG pipeline
                   (PyMuPDF → OCR →
                  bge-small → Chroma)
                      │
                 ML Engine
           (RandomForest + PyTorch)
```

---

## Quick Start

```bash
# 1. Clone & configure
cp .env.example .env        # add GEMINI_API_KEY (see below)

# 2. Docker (recommended)
docker compose up --build   # frontend → :3000  |  backend → :8000

# 3. Local dev
cd backend
python -m venv .venv && .venv\Scripts\activate   # Windows
pip install -r requirements.txt
python seed_demo.py
uvicorn app.main:app --reload --port 8000

# new terminal
cd frontend
npm install
set NEXT_PUBLIC_API=http://localhost:8000
npm run dev
```

---

## Environment & Keys

| Key | Where | Purpose |
|---|---|---|
| `GEMINI_API_KEY` | `.env` | Primary LLM — free key at [aistudio.google.com/apikey](https://aistudio.google.com/apikey) |
| `OLLAMA_URL` | `.env` | Local/offline fallback — `ollama pull llama3.2` then set `DEFAULT_PROVIDER=ollama` |
| `DATABASE_URL` | `.env` | SQLite default; swap to `postgresql+psycopg2://...` + `pip install psycopg2-binary` |
| `send_email()` | `backend/app/agents/tools.py` | Currently mocked; replace with SMTP / SendGrid / SES |

---

## App Flow

```
1. /brief      → Submit text + PDF  →  LangGraph runs to approval gate (pauses)
2. /approvals  → Approve / edit / reject  →  Graph resumes, executes, writes AuditLog
3. /            Control room dashboard
4. /attendee   RAG Q&A chat (escalates when confidence < 0.65)
5. /eval       Live benchmark — Chroma vs FAISS retrieval
```

---

## Tech Stack

| Layer | Technology | Why |
|---|---|---|
| **LLM — Cloud** | Google Gemini 2.5 Flash/Pro | Structured JSON output from messy briefs; low latency, generous free tier |
| **LLM — Local** | Ollama (llama3.2 / qwen2.5) | Zero data-leakage for confidential budgets & VIP lists; works fully offline |
| **Agentic Orchestration** | LangGraph + FastAPI | Stateful multi-step workflows with `interrupt()` / `Command(resume=...)` for safe HITL gates |
| **Frontend** | Next.js 14 + Tailwind CSS | App-router pages, SSE streaming, real-time approval queue UI |
| **Database** | SQLite → PostgreSQL | Zero-setup default; production-ready Postgres swap via one env var |
| **Document Parsing** | PyMuPDF (fitz) + Tesseract OCR | Extracts text from digital PDFs; falls back to OCR for scanned venue brochures & rate cards |
| **NLP** | spaCy + Sentence-Transformers | Named-entity extraction (dates, INR, headcount) and semantic chunking before embedding |
| **Embeddings** | BAAI/bge-small-en-v1.5 | Compact, fast multilingual embeddings tuned for retrieval |
| **Vector Store** | ChromaDB (prod) + FAISS (benchmark) | Metadata-filtered per-event retrieval; FAISS benchmarked for raw ANN speed |
| **RAG** | Semantic search + source citations | Retrieves only approved event chunks; triggers "escalate to human" when context is thin |
| **Classical ML** | Scikit-learn (RF / GBM) | No-show prediction, budget-overrun risk, vendor fit scoring — fast, explainable |
| **Neural Ranking** | PyTorch MLP / bi-encoder | Intent-aware attendee↔session matchmaking and domain-tuned embeddings |
| **Model Training** | Kaggle (T4/P100 GPU notebooks) | Trains tabular ML models on event attendance datasets without local GPU |
| **OSS Models** | Hugging Face Hub | Pulls `bge-small`, `bart-large-mnli` zero-shot classifier; hosts fine-tuned weights |
| **Containerization** | Docker Compose | One-command reproducible stack: Frontend + FastAPI + ChromaDB |
| **Evaluation** | RAGAS / LLM-as-judge | RAG faithfulness, Retrieval Recall@K, E2E latency p50/p95, Token cost per plan |

---

## Human-in-the-Loop (HITL) Safety

Every action with an external side-effect (sending emails, locking vendor quotes, publishing registration pages) **pauses** the LangGraph execution via `interrupt()`. The organizer approves, edits, or rejects on `/approvals`. Every decision is written to an append-only `AuditLog` (no updates/deletes).

---

## Known Limits & Roadmap

| Item | Status |
|---|---|
| Graph checkpointer | `MemorySaver` (in-memory) → swap to `langgraph-checkpoint-sqlite` for persistence across restarts |
| ML scores | Trained on synthetic data — retrain with real event logs before trusting numbers |
| Attendee ranker endpoint | `ml/matchmaker.py` is wired; API endpoint not yet exposed |
| Mobile companion | Flutter QR check-in app omitted from this build (same FastAPI endpoints) |

---

## Repo Layout

```
OrganizerAI/
├── backend/
│   ├── app/
│   │   ├── agents/        # LangGraph planner + tools (email, calendar, vendors)
│   │   ├── ml/            # RandomForest no-show predictor + PyTorch matchmaker
│   │   ├── rag/           # PDF ingest, OCR, ChromaDB/FAISS retriever
│   │   ├── main.py        # FastAPI routes + SSE
│   │   ├── database.py    # SQLAlchemy models (Event, AuditLog, Approval)
│   │   └── config.py      # Pydantic settings from .env
│   ├── seed_demo.py       # Loads sample events & vendors into DB
│   └── requirements.txt
├── frontend/
│   └── src/app/
│       ├── page.tsx       # Control room
│       ├── brief/         # Event brief intake
│       ├── approvals/     # HITL approval queue
│       ├── attendee/      # RAG Q&A chat
│       └── eval/          # Retrieval benchmark
├── eval/
│   └── benchmark.py       # RAGAS + latency evaluation script
├── docker-compose.yml
└── .env.example
```
