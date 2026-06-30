from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import requests
from app.routers import ingest, query, auth
from app.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        resp = requests.get(f"{settings.ollama_base_url}/api/tags", timeout=3)
        models = [m["name"] for m in resp.json().get("models", [])]
        print(f"Ollama is running. Available models: {models}")

        if settings.ollama_llm_model not in " ".join(models):
            print(f"Warning: '{settings.ollama_llm_model}' not found. Run: ollama pull {settings.ollama_llm_model}")
        if settings.ollama_embed_model not in " ".join(models):
            print(f"Warning: '{settings.ollama_embed_model}' not found. Run: ollama pull {settings.ollama_embed_model}")
    except Exception:
        print(f"Ollama not reachable at {settings.ollama_base_url}. Start it with: ollama serve")

    yield


app = FastAPI(
    lifespan=lifespan,
    title="Klaris API",
    description="Multi-source agentic RAG -- ingest GitHub repos, YouTube videos, and web pages into a unified knowledge base, then synthesize answers across all of them.",
    version="0.4.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/v1", tags=["Auth"])
app.include_router(ingest.router, prefix="/api/v1", tags=["Ingest"])
app.include_router(query.router, prefix="/api/v1", tags=["Query"])


@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "ok", "version": "0.4.0"}
