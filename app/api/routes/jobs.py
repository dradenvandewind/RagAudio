from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from app.schemas import JobStatus as JobStatusSchema
from app.models.job import JobStatus
from app.services.job_store import JobStore
from app.api.deps import get_job_store

router = APIRouter(tags=["jobs"])


@router.get("/status/{job_id}", response_model=JobStatusSchema)
def status(job_id: str, job_store: JobStore = Depends(get_job_store)):
    job = job_store.get(job_id)
    if not job:
        raise HTTPException(404, "Job inconnu")
    return JobStatusSchema(**job.model_dump())


@router.get("/srt/{job_id}")
def get_srt(job_id: str, job_store: JobStore = Depends(get_job_store)):
    job = job_store.get(job_id)
    if not job or job.status != JobStatus.DONE:
        raise HTTPException(404, "Sous-titres non disponibles")
    return FileResponse(job.srt_path, media_type="text/plain", filename=f"{job_id}.srt")