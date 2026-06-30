# Klaris — Multi-Source Agentic RAG Platform

Ingest GitHub repos, YouTube videos, and web articles into a unified
knowledge base. Ask questions across all of them at once, or explicitly
synthesize/compare what different sources say — fully local, powered by
Ollama (Llama 3.2 + nomic-embed-text), no API costs.

## Features

- **Multi-source ingestion** — GitHub repos, YouTube transcripts, web pages
- **RAG Q&A** — ask questions, get answers grounded in your ingested content
- **Cross-source synthesis** — explicitly compare what different sources say
- **JWT auth** — multi-tenant, each user's data is isolated
- **100% local LLM** — runs on Ollama, zero API costs

## Tech stack

FastAPI · LanceDB · Ollama (Llama 3.2, nomic-embed-text) · React (Vite) · Docker

********

## Option A — Run locally without Docker (development)

### Prerequisites
- Python 3.12
- Node.js 20+
- [Ollama](https://ollama.com) installed, with models pulled:
  ```bash
  ollama pull llama3.2:1b
  ollama pull nomic-embed-text
  ```

### Backend
```bash
python -m venv venv
.\venv\Scripts\activate          # Windows
# source venv/bin/activate       # Mac/Linux

pip install -r requirements.txt
copy .env.example .env           # Windows
# cp .env.example .env           # Mac/Linux

ollama serve                     # separate terminal
uvicorn app.main:app --reload
```

### Frontend (separate terminal)
```bash
cd frontend
npm install
npm run dev
```

Open **http://localhost:3000**.

---

## Option B — Run with Docker

Ollama itself is **not** containerized (GPU passthrough through Docker is
painful on most laptops) — it keeps running natively on your machine, and
the containers reach it via `host.docker.internal`.

### Prerequisites
- Docker Desktop
- Ollama running natively on your host with both models pulled (see above)

### Setup
```bash
cp .env.example .env
# Generate a real JWT secret and put it in .env:
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### Run
```bash
docker compose up --build
```

This starts:
- `klaris-api` on **http://localhost:8000** (FastAPI backend)
- `klaris-frontend` on **http://localhost:3000** (React, served statically)

Your vector data (`lancedb_data/`) and user accounts (`users_db.json`) are
mounted as volumes, so they persist across `docker compose down` / `up`.

To stop:
```bash
docker compose down
```

---

## API overview

| Method | Path                  | Auth required | Description |
|--------|------------------------|---------------|--------------|
| POST   | `/api/v1/auth/register` | No | Create an account, returns a JWT |
| POST   | `/api/v1/auth/login`    | No | Log in, returns a JWT |
| POST   | `/api/v1/ingest`        | Yes | Ingest a URL (GitHub/YouTube/web) |
| GET    | `/api/v1/sources`       | Yes | List your ingested sources |
| POST   | `/api/v1/query`         | Yes | Ask a question (blended search) |
| POST   | `/api/v1/synthesize`    | Yes | Compare/synthesize across sources |

Interactive docs: **http://localhost:8000/docs**

## Project structure

```
app/
├── main.py              # FastAPI app entry point
├── config.py             # Settings (reads .env)
├── auth/                 # JWT + password hashing, login-required guard
├── models/                # Pydantic schemas, user storage
├── routers/               # API endpoints (auth, ingest, query)
└── services/              # Core logic: fetchers, chunker, vector store, RAG, synthesis
frontend/                  # React (Vite) UI
```

## Known limitations (by design, for this portfolio scope)

- User storage is a JSON file, not a real database — fine for a demo,
  swap `app/models/user.py` for PostgreSQL in a production setting
- No async job queue yet — `/ingest` blocks until embedding finishes
- No live web search fallback — only answers from what you've ingested
