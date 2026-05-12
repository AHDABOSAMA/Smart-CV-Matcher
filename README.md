<div align="center">

# 🧠 Smart CV Matcher

### RAG-Powered Multilingual CV Analysis System

*Ask natural-language questions about candidates — in English **or** Arabic*

[![Python](https://img.shields.io/badge/Python-3.10-blue?logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![ChromaDB](https://img.shields.io/badge/ChromaDB-Vector_DB-orange)](https://www.trychroma.com)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker&logoColor=white)](https://docker.com)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)

</div>

---

## 📖 Overview

**Smart CV Matcher** is an end-to-end Retrieval-Augmented Generation (RAG) system that ingests raw, messy CV PDFs — English and Arabic — and answers recruiter questions about candidates using only the retrieved CV context, never hallucinating.

```
"Is this candidate suitable for a Data Analyst role?"
"What Python frameworks does Ahmed know?"
"ما هي المهارات التقنية لهذا المرشح؟"
```

The system is fully containerised with Docker and exposes a clean REST API built with FastAPI following the MVC pattern. Switching the LLM backend (Ollama, Gemini, OpenAI) requires a single config change.

---

## ✨ Features

| Feature | Details |
|---|---|
| 📄 **Raw PDF Ingestion** | Handles multi-column layouts, scanned docs, mixed-language files |
| 🔍 **Semantic Vector Search** | ChromaDB + cosine similarity via HNSW index |
| 🌍 **Arabic + English** | Multilingual embeddings, RTL extraction, Arabic text normalisation |
| 🏭 **LLM Factory Pattern** | Switch between Ollama (local), Gemini, or OpenAI with one env var |
| 🐳 **One-Command Deployment** | `docker-compose up --build` — no manual setup |
| 📑 **Auto API Docs** | Swagger UI at `/docs`, ReDoc at `/redoc` |
| ♻️ **Safe Re-upload** | Upsert strategy prevents duplicate chunks |

---

## 🏗️ Architecture

```
Client (curl / Postman / Browser)
         │
         ▼
┌─────────────────────────────────────┐
│       FastAPI Backend  :8001        │
│  ┌──────────┬──────────┬─────────┐  │
│  │ /health  │  /cv/*   │/query/  │  │  ← Controllers (MVC)
│  └──────────┴──────────┴─────────┘  │
│  ┌──────────────────────────────┐   │
│  │         Services Layer        │  │
│  │  pdf_parser   vector_store    │  │  ← Business Logic
│  │  llm_factory  rag_pipeline    │  │
│  └──────────────────────────────┘  │
│  ┌──────────────────────────────┐   │
│  │     Models / Schemas (Pydantic)│  │  ← Data Models
│  └──────────────────────────────┘  │
└─────────────────────────────────────┘
         │                │
         ▼                ▼
   ┌───────────┐   ┌──────────────────┐
   │ ChromaDB  │   │ Sentence-Trans.  │
   │ (vectors) │   │ MiniLM-L12-v2    │
   └───────────┘   └──────────────────┘
                          │
              ┌───────────┼───────────┐
              ▼           ▼           ▼
          Ollama       Gemini      OpenAI
        (local 🏠)   (free ☁️)   (paid ☁️)
```

### MVC Layer Breakdown

| Layer | Files | Responsibility |
|---|---|---|
| **Model** | `app/models/schemas.py` | Pydantic request/response shapes & validation |
| **Controller** | `app/api/*.py` | HTTP routing, error handling |
| **Service** | `app/services/*.py` | PDF parsing, embedding, RAG, LLM calls |
| **Config** | `app/core/config.py` | All settings via environment variables |

---

## 🚀 Quick Start

### Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed and running
- At least **4 GB RAM** allocated to Docker *(Settings → Resources)*
- Internet connection for the first build

### 1 — Clone & configure

```bash
git clone https://github.com/your-username/smart-cv-matcher.git
cd smart-cv-matcher
cp .env.example .env
```

Edit `.env` and set your preferred LLM provider and API keys (see [Configuration](#️-configuration)).

### 2 — Build & start

```bash
docker-compose up --build
```

This spins up two services:
- `smart-cv-matcher` — FastAPI backend on **port 8001**
- `ollama` — Local LLM server on **port 11434**

### 3 — Pull the LLM model *(first time only)*

```bash
docker exec ollama ollama pull llama3.2:1b
```

### 4 — Open the API

| Interface | URL |
|---|---|
| Swagger UI | http://localhost:8001/docs |
| ReDoc | http://localhost:8001/redoc |
| Health check | http://localhost:8001/health |

---

## ⚙️ Configuration

All settings live in `.env`. Copy `.env.example` to get started:

```env
# ── LLM Provider ───────────────────────────────────────────
# Options: "ollama" | "gemini" | "openai"
LLM_PROVIDER=ollama

# ── API Keys (only the active provider needs to be set) ────
GEMINI_API_KEY=your_gemini_key_here
OPENAI_API_KEY=your_openai_key_here

# ── Ollama (local, free, offline) ──────────────────────────
OLLAMA_BASE_URL=http://ollama:11434
OLLAMA_MODEL=llama3.2:1b

# ── Embeddings & Vector Store ───────────────────────────────
EMBEDDING_MODEL=sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2
CHROMA_PERSIST_DIR=./chroma_db
CHROMA_COLLECTION=cv_chunks

# ── Chunking ─────────────────────────────────────────────────
CHUNK_SIZE=400
CHUNK_OVERLAP=50
TOP_K=5
```

**Switching LLM providers** — change one line, no code changes needed:

```env
LLM_PROVIDER=gemini   # or "openai" or "ollama"
```

---

## 📡 API Reference

### `GET /health`

Returns system status, total chunk count, and active LLM provider.

```json
{
  "status": "ok",
  "total_chunks": 12,
  "llm_provider": "ollama",
  "embedding_model": "paraphrase-multilingual-MiniLM-L12-v2"
}
```

---

### `POST /cv/upload`

Upload a raw CV PDF for processing. Automatically detects language, parses, chunks, and stores embeddings.

```bash
curl -X POST http://localhost:8001/cv/upload \
  -F "file=@john_doe.pdf"
```

```json
{
  "filename": "john_doe.pdf",
  "chunks_added": 4,
  "language_detected": "en",
  "message": "CV processed and stored successfully"
}
```

---

### `GET /cv/list`

List all uploaded CVs currently in the vector store.

```json
{
  "cvs": ["john_doe.pdf", "arabic_cv_ahmed.pdf"],
  "total": 2
}
```

---

### `DELETE /cv/{filename}`

Remove a CV and all its associated chunks from the vector store.

```bash
curl -X DELETE http://localhost:8001/cv/john_doe.pdf
```

---

### `POST /query/ask` ⭐

The main RAG endpoint. Accepts a natural-language question and returns a grounded answer with source chunks.

**Request:**

```json
{
  "question": "Is this candidate suitable for a Data Analyst role?",
  "cv_filename": "john_doe.pdf",
  "top_k": 5,
  "llm_provider": "ollama"
}
```

| Field | Type | Required | Description |
|---|---|---|---|
| `question` | string | ✅ | Natural-language query (English or Arabic) |
| `cv_filename` | string | ❌ | Filter search to one CV; omit to search all |
| `top_k` | int | ❌ | Chunks to retrieve (default: 5) |
| `llm_provider` | string | ❌ | Override the default LLM for this request |

**Response:**

```json
{
  "question": "Is this candidate suitable for a Data Analyst role?",
  "answer": "Based on the CV, the candidate has 3 years of experience with Python and SQL, has completed two data analysis internships, and holds a degree in Computer Science. They appear well-suited for a junior Data Analyst role.",
  "llm_provider": "ollama",
  "retrieved_chunks": [
    {
      "text": "Skills: Python, SQL, Power BI, pandas, NumPy...",
      "source": "john_doe.pdf",
      "page": 1,
      "score": 0.87
    }
  ],
  "total_chunks_searched": 5
}
```

---

## 🔬 How It Works

### Chunking Strategy

CVs are split using a **word-based sliding window**:

| Parameter | Value | Why |
|---|---|---|
| Chunk size | 400 tokens | Covers one full CV section without losing retrieval precision |
| Overlap | 50 tokens | Prevents sentences from losing meaning when split across chunks |
| Method | Per-page sliding window | Language-agnostic; works for both Arabic and English |

> A 500-token chunk on a single-page CV often captures the entire CV as one chunk, making retrieval useless. At 400 + 50 overlap, a typical CV produces 2–4 focused chunks.

### Embedding Model

`paraphrase-multilingual-MiniLM-L12-v2` — chosen because:
- Supports **50+ languages including Arabic** natively in one model
- Runs on CPU with no GPU required (~120 MB)
- Trained on parallel multilingual corpora → true cross-lingual search
- 384-dimensional vectors with cosine similarity

### RAG Pipeline

```
User Query
    │
    ▼
[1] Embed query with the same multilingual model
    │
    ▼
[2] Vector search → top-k chunks by cosine similarity
    │
    ▼
[3] Inject chunks into structured LLM prompt
    │
    ▼
[4] LLM generates grounded answer (no hallucination by instruction)
    │
    ▼
Answer + source chunks returned via API
```

### Arabic NLP Pipeline

| Step | Technique |
|---|---|
| Detection | Unicode range check U+0600–U+06FF |
| Diacritics | Strip tashkeel (U+064B–U+065F) |
| Alef normalisation | `أإآٱ` → `ا` |
| Ya normalisation | `ى` → `ي` |
| Ta Marbuta | `ة` → `ه` |

### LLM Factory Pattern

```python
# Add a new provider in one place, zero changes elsewhere
LLM_REGISTRY = {
    "ollama": OllamaLLM,
    "gemini": GeminiLLM,
    "openai": OpenAILLM,
    # "anthropic": AnthropicLLM,  ← just add this
}
```

---

## 🗂️ Project Structure

```
smart-cv-matcher/
├── app/
│   ├── api/
│   │   ├── cv_routes.py        # CV upload / list / delete endpoints
│   │   ├── query_routes.py     # RAG query endpoint
│   │   └── health.py           # Health check
│   ├── core/
│   │   └── config.py           # Settings from .env
│   ├── models/
│   │   └── schemas.py          # Pydantic request/response models
│   ├── services/
│   │   ├── pdf_parser.py       # PDF ingestion + Arabic normalisation
│   │   ├── vector_store.py     # ChromaDB wrapper
│   │   ├── llm_factory.py      # Factory pattern: Ollama / Gemini / OpenAI
│   │   └── rag_pipeline.py     # Full RAG orchestration
│   └── main.py                 # FastAPI app + router registration
├── data/
│   └── cvs/                    # Uploaded CV PDFs (Docker volume)
├── chroma_db/                  # Persisted vector embeddings (Docker volume)
├── tests/
│   └── test_api.py             # Quick API smoke tests
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── .env.example
```

---

## 🧪 Running Tests

With the server running, execute the smoke-test script:

```bash
python tests/test_api.py
```

This tests the health check, CV listing, and an English + Arabic query end-to-end.

---

## ⚠️ Known Limitations & Edge Cases

| Case | Behaviour | Workaround |
|---|---|---|
| Arabic query → English CV | LLM responds in English; similarity drops ~60% | Use Gemini (handles Arabic generation better) |
| Arabic CV generated by reportlab | Text extracts as garbled Latin-1 | Use CVs exported from Word / Acrobat |
| English query → Arabic CV | Correct answer, but lower similarity score | Hybrid index English skill tokens separately |
| Very long CVs (>3 pages) | May produce 6+ chunks, slowing retrieval | Reduce `CHUNK_SIZE` to 300 in `.env` |

---

## 🗺️ Roadmap

- [ ] Re-ranking layer (cross-encoder) for improved retrieval precision
- [ ] Hybrid BM25 + vector search for keyword-heavy queries
- [ ] Batch upload endpoint for ingesting entire CV folders
- [ ] Per-query Arabic/English language auto-detection for LLM selection
- [ ] Frontend UI (React) for recruiter-facing queries

---

## 📄 License

MIT — see [LICENSE](LICENSE) for details.

---

<div align="center">

Built with ❤️ using FastAPI · ChromaDB · Sentence-Transformers · Ollama

</div>
