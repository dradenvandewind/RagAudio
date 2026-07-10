"""
FastAPI API: Dailymotion (yt-dlp/ffmpeg) -> Whisper (SRT) -> LlamaIndex (RAG)

Run with:
    uvicorn app.main:app --reload

Interactive docs: http://localhost:8000/docs
"""
import uuid
from pathlib import Path

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse

from app.schemas import IngestRequest, IngestResponse, AskRequest, AskResponse, JobStatus
from app.services.downloader import download_audio
from app.services.transcriber import transcribe_to_srt
from app.services.rag_engine import RAGEngine

BASE_DIR = Path("data")
AUDIO_DIR = BASE_DIR / "audio"
SRT_DIR = BASE_DIR / "srt"
for d in (AUDIO_DIR, SRT_DIR):
    d.mkdir(parents=True, exist_ok=True)

app = FastAPI(
    title="Audio RAG API",
    description="Video ingestion -> transcription -> RAG with LlamaIndex",
    version="1.0.0",
)

rag = RAGEngine(persist_dir=str(BASE_DIR / "index"))

# In-memory job storage (replace with Redis/DB in production)
JOBS: dict[str, dict] = {}


def _process_video(job_id: str, url: str, language: str, whisper_model: str):
    """Full pipeline executed as a background task."""
    try:
        JOBS[job_id]["status"] = "downloading"
        audio_path = download_audio(url, str(AUDIO_DIR / job_id))

        JOBS[job_id]["status"] = "transcribing"
        srt_path = str(SRT_DIR / f"{job_id}.srt")
        result = transcribe_to_srt(
            audio_path, srt_path, language=language, model_name=whisper_model
        )

        JOBS[job_id]["status"] = "indexing"
        rag.add_document(
            doc_id=job_id,
            text=result["text"],
            metadata={"source_url": url, "srt_path": srt_path},
        )

        JOBS[job_id].update(
            {"status": "done", "srt_path": srt_path, "text_preview": result["text"][:300]}
        )
    except Exception as e:
        JOBS[job_id]["status"] = "error"
        JOBS[job_id]["error"] = str(e)


@app.post("/ingest", response_model=IngestResponse)
def ingest(req: IngestRequest, background_tasks: BackgroundTasks):
    """Start the full pipeline for a Dailymotion URL (asynchronous)."""
    job_id = str(uuid.uuid4())
    JOBS[job_id] = {"status": "queued", "url": str(req.url)}
    background_tasks.add_task(
        _process_video, job_id, str(req.url), req.language, req.whisper_model
    )
    return IngestResponse(job_id=job_id, status="queued")


@app.get("/status/{job_id}", response_model=JobStatus)
def status(job_id: str):
    """Check the status of a job (queued / downloading / transcribing / indexing / done / error)."""
    job = JOBS.get(job_id)
    if not job:
        raise HTTPException(404, "Job inconnu")
    return JobStatus(job_id=job_id, **job)


@app.get("/srt/{job_id}")
def get_srt(job_id: str):
    """Download the generated .srt subtitle file."""
    job = JOBS.get(job_id)
    if not job or job.get("status") != "done":
        raise HTTPException(404, "Sous-titres non disponibles")
    return FileResponse(job["srt_path"], media_type="text/plain", filename=f"{job_id}.srt")


@app.post("/ask", response_model=AskResponse)
def ask(req: AskRequest):
    """Query the indexed corpus (RAG) across all ingested videos."""
    answer, sources = rag.query(req.question, top_k=req.top_k)
    return AskResponse(answer=answer, sources=sources)


@app.get("/")
def root():
    return {"message": "Audio RAG API — voir /docs pour la documentation interactive"}
