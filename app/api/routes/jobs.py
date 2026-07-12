import asyncio
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from app.schemas import JobStatus as JobStatusSchema
from app.models.job import JobStatus
from app.services.job_store import JobStore
from app.api.deps import get_job_store
from app.services.translator import translate_srt_file
from pathlib import Path

router = APIRouter(tags=["jobs"])


@router.get("/status/{job_id}", response_model=JobStatusSchema)
async def status(job_id: str, job_store: JobStore = Depends(get_job_store)):
    job = await job_store.get(job_id)
    if not job:
        raise HTTPException(404, "Job inconnu")
    return JobStatusSchema(**job.model_dump())


@router.get("/srt/{job_id}")
async def get_srt(job_id: str, job_store: JobStore = Depends(get_job_store)):
    job = await job_store.get(job_id)
    if not job or job.status != JobStatus.DONE:
        raise HTTPException(404, "Sous-titres non disponibles")
    return FileResponse(job.srt_path, media_type="text/plain", filename=f"{job_id}.srt")


@router.get("/srt/{job_id}/translate")
async def get_srt_translated(
    job_id: str,
    target_lang: str = "en",
    job_store: JobStore = Depends(get_job_store),
):
    job = await job_store.get(job_id)
    if not job or job.status != JobStatus.DONE:
        raise HTTPException(404, "Sous-titres non disponibles")

    src_path = Path(job.srt_path)
    out_path = src_path.with_name(f"{src_path.stem}_{target_lang}{src_path.suffix}")

    if not out_path.exists():
        # translate_srt_file is synchronous and blocking (calls the Ollama
        # HTTP API and can take a while for long files): offload it so it
        # doesn't stall the event loop for other requests.
        await asyncio.to_thread(
            translate_srt_file, str(src_path), str(out_path), target_lang=target_lang
        )

    return FileResponse(
        str(out_path),
        media_type="text/plain",
        filename=f"{job_id}_{target_lang}.srt",
    )