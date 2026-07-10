"""
FastAPI API: Dailymotion (yt-dlp/ffmpeg) -> Whisper (SRT) -> LlamaIndex (RAG)

Run with:
    uvicorn app.main:app --reload

Docs interactives: http://localhost:8000/docs
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI

from app.core.config import settings
from app.core.logging import setup_logging
from app.services.job_store import JobStore
from app.services.rag_engine import RAGEngine
from app.api.routes import ingest, jobs, ask


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    settings.ensure_dirs()
    app.state.job_store = JobStore()
    app.state.rag = RAGEngine(persist_dir=str(settings.index_dir))
    yield
    # cleanup if needed (close connections, etc.)


app = FastAPI(
    title="Audio RAG API",
    description="Video ingestion -> transcription -> RAG with LlamaIndex",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(ingest.router)
app.include_router(jobs.router)
app.include_router(ask.router)


@app.get("/")
def root():
    return {"message": "Audio RAG API — voir /docs pour la documentation interactive"}