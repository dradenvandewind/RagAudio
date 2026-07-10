import uuid
from fastapi import APIRouter, BackgroundTasks, Depends
from app.schemas import IngestRequest, IngestResponse
from app.services.job_store import JobStore
from app.services.rag_engine import RAGEngine
from app.services.pipeline import process_video
from app.api.deps import get_job_store, get_rag_engine

router = APIRouter(tags=["ingest"])


@router.post("/ingest", response_model=IngestResponse)
def ingest(
    req: IngestRequest,
    background_tasks: BackgroundTasks,
    job_store: JobStore = Depends(get_job_store),
    rag: RAGEngine = Depends(get_rag_engine),
):
    """Démarre le pipeline complet pour une URL Dailymotion (asynchrone)."""
    job_id = str(uuid.uuid4())
    job_store.create(job_id, url=str(req.url))

    background_tasks.add_task(
        process_video,
        job_id,
        str(req.url),
        req.language,
        req.whisper_model,
        job_store,
        rag,
    )
    return IngestResponse(job_id=job_id, status="queued")