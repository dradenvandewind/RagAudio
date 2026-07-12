import asyncio
import logging
from app.core.config import settings
from app.models.job import JobStatus
from app.services.job_store import JobStore
from app.services.downloader import download_audio
from app.services.transcriber import transcribe_to_srt
from app.services.rag_engine import RAGEngine

logger = logging.getLogger("audio_rag.pipeline")


async def process_video(
    job_id: str,
    url: str,
    language: str,
    whisper_model: str,
    job_store: JobStore,
    rag: RAGEngine,
) -> None:
    """Complete pipeline executed as a background task."""
    try:
        await job_store.update(job_id, status=JobStatus.DOWNLOADING)
        audio_path = await download_audio(url, str(settings.audio_dir / job_id))

        await job_store.update(job_id, status=JobStatus.TRANSCRIBING)
        srt_path = str(settings.srt_dir / f"{job_id}.srt")
        # transcribe_to_srt is CPU-bound (Whisper) and synchronous: run it in a
        # worker thread so it doesn't block the event loop while it runs.
        result = await asyncio.to_thread(
            transcribe_to_srt,
            audio_path,
            srt_path,
            language=language,
            model_name=whisper_model,
            device="cpu",
        )

        await job_store.update(job_id, status=JobStatus.INDEXING)
        # rag.add_document is likely also blocking (embedding calls, disk I/O);
        # offload it too so it doesn't stall other requests.
        await asyncio.to_thread(
            rag.add_document,
            doc_id=job_id,
            text=result["text"],
            metadata={"source_url": url, "srt_path": srt_path},
        )

        await job_store.update(
            job_id,
            status=JobStatus.DONE,
            srt_path=srt_path,
            text_preview=result["text"][:300],
        )
        logger.info("Job %s completed successfully", job_id)

    except Exception as e:
        logger.exception("Job %s failed", job_id)
        await job_store.set_error(job_id, str(e))