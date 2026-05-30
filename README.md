<div align="center">

<img width="900" height="500" alt="landing" src="https://github.com/user-attachments/assets/2720736f-776f-4813-8181-383622b4e709" />

<br/>

# DocRAG

**An 8-node LangGraph RAG pipeline that turns any business PDF into a cited, verified answer — running entirely on your own machine.**

No OpenAI key. No cloud bill. No hallucinated tax figures.

<br/>

[![Python](https://img.shields.io/badge/Python-3.12-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![LangGraph](https://img.shields.io/badge/LangGraph-Agentic_RAG-7b2ff7?style=flat-square)](https://langchain-ai.github.io/langgraph)
[![Next.js](https://img.shields.io/badge/Next.js-16-black?style=flat-square&logo=next.js)](https://nextjs.org)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-336791?style=flat-square&logo=postgresql&logoColor=white)](https://postgresql.org)
[![ChromaDB](https://img.shields.io/badge/ChromaDB-Vector_Store-00c9a7?style=flat-square)](https://trychroma.com)
[![Ollama](https://img.shields.io/badge/Ollama-Llama_3.3_8B-FF6B35?style=flat-square)](https://ollama.ai)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?style=flat-square&logo=docker&logoColor=white)](https://docker.com)
[![License](https://img.shields.io/badge/License-MIT-22c55e?style=flat-square)](LICENSE)

<br/>

**87.4% Python · 9.1% TypeScript · 45+ files · Python 3.12 · One command deploy**

</div>

---

## What This Is

India has 63 million SMEs. Most of them wrestle with the same stack of paperwork every month — GST invoices, HSN code schedules, vendor contracts, compliance notices. Getting answers out of those documents means either hiring a CA, spending hours reading, or getting burned by generic AI that makes up tax figures.

DocRAG is built for exactly that gap. Drop a PDF into it, ask a question in plain English, and get back a grounded answer that tells you the page number, the source chunk, and a confidence score. The model never generates from memory — every sentence in the response is anchored to something it actually read.

The entire stack runs locally. GST documents and vendor contracts don't leave your machine.

---

## Table of Contents

- [Live UI Preview](#live-ui-preview)
- [How the Pipeline Works](#how-the-pipeline-works)
- [Document Ingestion](#document-ingestion)
- [GST Intelligence Engine](#gst-intelligence-engine)
- [Security Architecture](#security-architecture)
- [Infrastructure](#infrastructure)
- [Project Structure](#project-structure)
- [API Reference](#api-reference)
- [Performance](#performance)
- [Running It](#running-it)
- [Design Decisions](#design-decisions)

---

## Live UI Preview

### Chat Interface

The main working surface. Left sidebar shows your uploaded documents. Center is the conversation. Right panel pins the source chunks that grounded each answer so you can verify every claim.

<img width="900" height="500" alt="chat_ui" src="https://github.com/user-attachments/assets/798f7d17-58d4-43aa-8ef5-4c048bea8d37" />

---

### Document Upload & Processing

Drag a PDF in, watch the ingestion pipeline run in real time: Docling parse → semantic chunking → sentence-transformer embeddings → ChromaDB storage. Status flips to `ready` the moment it's queryable.

<img width="900" height="500" alt="upload_flow" src="https://github.com/user-attachments/assets/cba56df0-46d3-4be9-b1a2-a0efbe75a174" />

---

### Admin Dashboard

Full system visibility: query volume charts, per-user activity, document counts, latency trending, and the compliance audit trail. Built for whoever's running this for their team.

<img width="900" height="500" alt="admin_dashboard" src="https://github.com/user-attachments/assets/ac9bac07-d1bd-4e6f-a3da-d7db1ffae001" />

---

## How the Pipeline Works

<img width="900" height="500" alt="rag_pipeline" src="https://github.com/user-attachments/assets/62386bfd-5779-4507-861e-43f9de8160c6" />

The query-to-answer path is a LangGraph state machine — not a chain. That distinction matters: a chain dies linearly, a state machine can retry, branch, and fail individual nodes without corrupting everything downstream.

<img width="1593" height="914" alt="image" src="https://github.com/user-attachments/assets/43ab3842-1757-455d-ba27-226308a84a24" />

**Node-by-node:**

| # | Node | What it actually does |
|---|------|-----------------------|
| 1 | **Query Expand** | Rewrites the input into multiple semantic variants using HyDE (Hypothetical Document Embeddings). One question becomes 5 search vectors. Dramatically improves recall on sparse or ambiguous queries. |
| 2 | **Hybrid Retrieval** | Fires both ChromaDB vector similarity (384-dim `sentence-transformers`) and BM25 keyword search in parallel. Results are merged and filtered by `user_id` — one user's documents are invisible to another. |
| 3 | **Reranking** | A cross-encoder scores every candidate chunk against the original query. This is the precision pass — it cuts noise that vector similarity routinely lets through. |
| 4 | **Generation** | Ollama running `llama3.3:8b` locally. The model receives only the reranked context and a strict prompt that requires citing page numbers. It cannot make things up because it has no other source. |
| 5 | **GST Tools** | Tool-calling node that fires four domain-specific functions: GSTIN validation, HSN extraction, tax calculation, and legal risk detection. Runs only when the document is financial. |
| 6 | **Self-Verification** | The model re-reads its own answer against source context. RAGAS faithfulness check. If score drops below threshold, the node retries with tighter context. |
| 7 | **Format** | Structures the final output as `{answer, sources: [{doc_id, page, chunk_text}], confidence}`. This is what the frontend renders. |
| 8 | **Audit Log** | Writes every query to the `AuditLog` PostgreSQL table via `structlog`. Immutable compliance trail, queryable by admins. |

---

## Document Ingestion

<img width="1896" height="389" alt="image" src="https://github.com/user-attachments/assets/548b152e-9e26-419a-8dc6-0be6fb8eddc7" />

**Why Docling instead of Unstructured?**

Unstructured extracts text. Docling understands document structure — it knows a table is a table, not a paragraph, and preserves that relationship through chunking. For a GST invoice with a tax breakdown table, that difference between "a bunch of numbers in a paragraph" and "a structured table with row/column relationships" is the difference between a useful answer and a wrong one.

The ingestion service runs as a FastAPI background task. The user gets an immediate `202 Accepted` with a document ID. They can poll `/api/documents/{id}` for status, or the frontend polls automatically every 3 seconds.

```
POST /api/documents
→ 202 Accepted  { "doc_id": "uuid", "status": "processing" }

# Background task runs:
PDF → Docling parse → semantic chunks → sentence-transformers (384d)
   → ChromaDB (namespaced by user_id) → doc.status = "ready"
   → AuditLog.write("document_ingested")
```

Processing time: under 30 seconds for a 50-page PDF on CPU.

---

## GST Intelligence Engine

<img width="900" height="500" alt="gst_tools" src="https://github.com/user-attachments/assets/130f29f2-abcd-4c49-ad63-1ee09569c60b" />

`services/gst_tools.py` is the part that makes this actually useful for Indian businesses instead of just another PDF chatbot. Four tools, all under 150ms, zero external API calls.

**GSTIN Validator**
Regex `[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}` plus state code lookup against all 37 states/UTs. Returns validity, state name, and entity type extracted from character positions.

**HSN Code Extractor**
Pattern-matches 4, 6, and 8-digit HSN codes from document text. Returns each code with its surrounding sentence so the user knows exactly where it appeared and in what context.

**Tax Calculator**
Given base amount and GST rate, computes CGST/SGST (intra-state) or IGST (inter-state) breakdown. Handles both exclusive and tax-inclusive amounts. Fast enough to run mid-pipeline without adding perceptible latency.

**Legal Risk Detector**
Scans for risk keywords across three tiers. High-risk (`penalty`, `legal action`, `court`, `arbitration`, `criminal`) triggers a prominent warning. Medium-risk (`dispute`, `default`, `breach`) gets flagged for review. Every flagged term comes back with its source sentence and page number.

---

## Security Architecture

<img width="900" height="500" alt="auth_security" src="https://github.com/user-attachments/assets/58fb8e1e-946d-4132-8a52-d9609cef8c84" />

Authentication and access control runs at four independent enforcement layers — any single layer failing doesn't mean access is granted.

**Layer 1 — Rate Limiting (middleware)**
60 requests per minute per IP. Returns `429 Too Many Requests` with a `Retry-After` header. Applied before any authentication check, so it also throttles unauthenticated probing.

**Layer 2 — JWT Authentication (middleware)**
`Authorization: Bearer <token>` on every protected route. Tokens are signed HS256, 24-hour expiry. The middleware decodes and validates before the request reaches any router. Invalid or expired tokens get a hard `401`.

**Layer 3 — RBAC (FastAPI Depends)**
Every admin route has `Depends(require_admin)` injected. The dependency reads `current_user.role` and raises `403` if it's not `"admin"`. User routes use `Depends(get_current_user)` which just confirms a valid token exists.

**Layer 4 — Multi-tenant data isolation (DB + ChromaDB)**
Two simultaneous filters. Every database query has `WHERE user_id = :current_user_id` — no raw queries, no ORM methods that bypass this. Every ChromaDB retrieval passes `where={"user_id": current_user_id}` as a metadata filter. Neither layer alone is sufficient; both are required. A user who somehow bypasses the DB filter still hits the ChromaDB filter, and vice versa.

Passwords: bcrypt with default cost factor (12). The only file that touches plaintext passwords is `core/security.py`.

---

## Infrastructure

<img width="900" height="500" alt="docker_infra" src="https://github.com/user-attachments/assets/9687c998-2a54-494a-9bff-66c2e4922528" />

Four Docker services orchestrated by a single `docker-compose.yml`. First-run pulls the Llama 3.3 8B model (~4.7GB), which takes 5–10 minutes. Every subsequent start is fast.

<img width="1902" height="441" alt="image" src="https://github.com/user-attachments/assets/fa684af5-ed9c-4323-9e3d-5702dbd7b2e7" />

| Service | Image | Port | Role |
|---------|-------|------|------|
| `rag-frontend` | `node:18-alpine` | 3000 | Next.js 16 UI |
| `rag-backend` | `python:3.12-slim` | 8000 | FastAPI + LangGraph |
| `rag-ollama` | `ollama/ollama` | 11434 | Local LLM inference |
| `rag-postgres` | `postgres:16` | 5432 | Relational + audit store |

Persistent volumes: `postgres_data`, `chroma_data` (embedded, inside backend container), `ollama_models`.

Health checks: PostgreSQL checks every 10s. Ollama has a 30s check interval with a 5-minute startup grace period for model pull. Backend waits on both `postgres` and `ollama` via `depends_on: condition: service_healthy`.

---

## Project Structure

```
DocRAG/
│
├── backend/
│   ├── app/
│   │   ├── main.py                     # FastAPI app factory, CORS, lifespan, middleware
│   │   ├── core/
│   │   │   ├── config.py               # Pydantic Settings — reads .env, all typed
│   │   │   ├── database.py             # Async SQLAlchemy engine, session factory
│   │   │   └── security.py             # JWT encode/decode + bcrypt — only file touching passwords
│   │   │
│   │   ├── models/                     # SQLAlchemy ORM models (all async)
│   │   │   ├── user.py                 # id, email, hashed_password, role, created_at
│   │   │   ├── document.py             # id, user_fk, filename, status, page_count, chunk_count
│   │   │   ├── chat.py                 # ChatSession (has many ChatMessages)
│   │   │   └── audit.py               # AuditLog — user, action, metadata JSON, timestamp
│   │   │
│   │   ├── schemas/                    # Pydantic v2 request/response contracts
│   │   │   ├── auth.py                 # LoginRequest, RegisterRequest, TokenResponse
│   │   │   ├── document.py             # UploadResponse, DocumentStatus, DocumentList
│   │   │   └── chat.py                 # ChatRequest, ChatResponse, SourceChunk
│   │   │
│   │   ├── routers/
│   │   │   ├── auth.py                 # POST /register /login /refresh  GET /me
│   │   │   ├── upload.py               # POST /documents  GET /documents /documents/{id}
│   │   │   ├── chat.py                 # POST /chat  GET /sessions /sessions/{id}
│   │   │   └── admin.py               # GET /users /metrics /logs  (admin-only)
│   │   │
│   │   ├── services/
│   │   │   ├── rag_agent.py            # 8-node LangGraph state machine (~400 lines)
│   │   │   ├── ingestion.py            # Docling → chunker → embedder → ChromaDB
│   │   │   ├── embeddings.py           # sentence-transformers wrapper, batch processing
│   │   │   ├── chroma_client.py        # ChromaDB singleton, multi-tenant query interface
│   │   │   └── gst_tools.py            # GSTIN validator, HSN extractor, tax calc, risk detector
│   │   │
│   │   └── utils/
│   │       ├── logger.py               # structlog configuration — structured JSON logs
│   │       └── validators.py           # Input sanitization, file size/type checks
│   │
│   ├── alembic/                        # Database migrations
│   │   ├── env.py
│   │   └── versions/                   # Revision history
│   │
│   ├── tests/
│   │   ├── conftest.py                 # pytest fixtures, test DB setup
│   │   └── test_auth.py               # Auth flow tests
│   │
│   ├── requirements.txt               # 45 pinned dependencies
│   ├── .env.example                   # All env vars documented with defaults
│   └── Dockerfile                     # python:3.12-slim, non-root user
│
├── frontend/
│   ├── app/
│   │   ├── page.tsx                    # Landing (animated gradient hero, feature pills)
│   │   ├── login/page.tsx             # Login form — Zod schema, Framer Motion transitions
│   │   └── register/page.tsx          # Registration — same stack
│   ├── lib/
│   │   ├── api.ts                      # Axios instance, request/response interceptors, token refresh
│   │   └── utils.ts                    # cn() helper, date formatters
│   ├── globals.css                    # Tailwind config + glassmorphism utilities
│   ├── package.json                   # Next.js 16, React 19, Framer Motion, Zod, Axios
│   └── Dockerfile                     # node:18-alpine, standalone output
│
├── notebooks/
│   └── eval.ipynb                     # RAGAS faithfulness + nDCG@5 evaluation
│
├── docker-compose.yml                 # 4 services, volumes, health checks, depends_on
├── setup.sh                           # Linux/macOS bootstrap (chmod, env copy, pull model)
├── setup.bat                          # Windows bootstrap
├── SETUP.md                           # Quick start guide
├── DEPLOYMENT.md                      # Local / Render / Railway / Vercel options
└── PROJECT_SUMMARY.md                 # Architecture overview + metrics
```

---

## API Reference

All endpoints are prefixed `/api`. Interactive docs at `http://localhost:8000/api/docs`.

**Auth**
```
POST   /api/auth/register        body: {email, password, name}   → 201 {user_id, token}
POST   /api/auth/login           body: {email, password}          → 200 {token, refresh_token}
POST   /api/auth/refresh         body: {refresh_token}            → 200 {token}
GET    /api/auth/me              header: Bearer                   → 200 {id, email, role}
```

**Documents**
```
POST   /api/documents            multipart PDF (≤50MB)           → 202 {doc_id, status}
GET    /api/documents            header: Bearer                   → 200 [{id, name, status, pages}]
GET    /api/documents/{id}       header: Bearer                   → 200 {id, name, status, chunks}
DELETE /api/documents/{id}       header: Bearer                   → 204
```

**Chat**
```
POST   /api/chat                 body: {doc_id, query, session_id?}
                                 → 200 {answer, sources, confidence, session_id}
GET    /api/chat/sessions        header: Bearer                   → 200 [{id, doc_id, created_at}]
GET    /api/chat/sessions/{id}   header: Bearer                   → 200 {messages: [...]}
```

**Admin** *(role=admin required)*
```
GET    /api/admin/users          → 200 [{id, email, role, doc_count, query_count}]
GET    /api/admin/metrics        → 200 {queries_today, avg_latency_ms, doc_count, user_count}
GET    /api/admin/logs           → 200 [{user_id, action, metadata, timestamp}]
GET    /api/health               → 200 {status, postgres, ollama, chroma}
```

**Response shape for `/api/chat`:**
```json
{
  "answer": "The total GST liability on Invoice #2024-003 is ₹18,540 (CGST 9%: ₹9,270, SGST 9%: ₹9,270).",
  "sources": [
    {
      "doc_id": "uuid",
      "filename": "Invoice_2024-003.pdf",
      "page": 2,
      "section": "Tax Summary",
      "chunk_text": "Total taxable value: ₹1,03,000. CGST @ 9%: ₹9,270. SGST @ 9%: ₹9,270.",
      "score": 0.94
    }
  ],
  "confidence": 0.92,
  "session_id": "uuid",
  "latency_ms": 1342
}
```

---

## Performance

| Metric | Target | Achieved by |
|--------|--------|-------------|
| Retrieval nDCG@5 | > 0.85 | Hybrid vector + BM25 + cross-encoder reranking |
| RAGAS Faithfulness | > 0.90 | Self-verification node with automatic retry |
| Hallucination Rate | < 5% | Grounded prompts, citation enforcement, no memory generation |
| P50 Response Latency | < 2s | Async FastAPI, optimized ChromaDB queries, local Ollama |
| PDF Ingestion | < 30s / 50 pages | Docling + batched sentence-transformer inference |
| Rate Limit | 60 req/min | Starlette middleware, per-IP |

Evaluation methodology lives in `notebooks/eval.ipynb` using the RAGAS framework on a test set of 50 GST documents with manually verified ground-truth answers.

---

## Running It

**Requirements:** Docker Desktop, 8GB+ RAM, 10GB+ disk, Git.

```bash
git clone https://github.com/sat1828/DocRAG.git
cd DocRAG
docker-compose up --build
```

First run downloads `llama3.3:8b` (~4.7GB). Takes 5–10 minutes once, never again.

```
http://localhost:3000          # Frontend
http://localhost:8000/api/docs # Swagger UI
http://localhost:8000/api/health

Default admin: admin@demo.com  /  Admin@123
```

**Without Docker (dev mode):**

```bash
# Backend
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
alembic upgrade head
uvicorn app.main:app --reload   # http://localhost:8000

# Frontend (new terminal)
cd frontend
npm install
npm run dev                     # http://localhost:3000

# Ollama (new terminal, install from ollama.ai)
ollama pull llama3.3:8b
ollama serve
```

**Troubleshoot:**

```bash
# Port conflicts
docker-compose down && docker-compose up --build

# Reset everything, wipe all data
docker-compose down -v
docker-compose up --build

# Pull Ollama model manually if auto-pull fails
docker exec -it rag-ollama ollama pull llama3.3:8b

# View logs
docker logs rag-backend -f
docker logs rag-postgres -f

# Run tests
cd backend && pytest tests/ -v
```

---

## Design Decisions

**Why LangGraph instead of a LangChain chain?**

A `chain.invoke()` is a linear pipeline that fails atomically. LangGraph is a state machine with conditional edges — each node is independently debuggable, can retry on failure, can branch based on document type (skip GST tools if it's not a financial PDF), and the full intermediate state is inspectable at every step. The 8-node graph also makes it trivial to add new nodes (e.g., a table extraction specialist, or a multi-document cross-reference node) without touching any existing logic.

**Why Docling over Unstructured?**

Both extract text from PDFs. Docling also understands layout — it knows a table is a table and preserves row/column relationships through the chunking step. For Indian GST invoices, which are dense with multi-column tax tables, this isn't a nice-to-have. The difference between "a paragraph of numbers" and "a structured table with CGST/SGST/IGST clearly separated" determines whether the tax calculator gets correct inputs.

**Why local Ollama instead of the OpenAI API?**

Two reasons that both matter for the target market. First, Indian SME financial documents — GST returns, vendor invoices, legal contracts — contain sensitive business data that shouldn't leave the organization's infrastructure. Second, running Llama 3.3 8B locally costs nothing per query after the one-time hardware cost. The OpenAI equivalent would be non-trivial at scale for a business processing hundreds of documents monthly.

**Why ChromaDB instead of Pinecone or Weaviate?**

No managed service fees, no egress costs, no account setup, no vendor lock-in. For a local-first deployment built for small businesses that don't have cloud infrastructure teams, self-hosted embedded ChromaDB is the operationally correct choice. The tradeoff is no horizontal scaling — acceptable for the single-tenant or small-team use case this is designed for.

**Why the dual-layer multi-tenancy model?**

A single filter at either the database or the vector store level could theoretically be bypassed by a bug, a missed `WHERE` clause in a new query, or an ORM method that doesn't apply filters. By enforcing `user_id` isolation at both layers simultaneously, a bug in one layer doesn't expose another user's data — the second layer still catches it. Defense in depth applied to a real threat.

---

<div align="center">

**DocRAG** · Built 2026 · Python 87.4% · TypeScript 9.1% · MIT License

[GitHub](https://github.com/sat1828/DocRAG) · [API Docs](http://localhost:8000/api/docs) · [SETUP.md](SETUP.md) · [DEPLOYMENT.md](DEPLOYMENT.md)

</div>
