import logging
from app.core.config import settings
from app.models.job import JobStatus
from app.services.job_store import JobStore
from app.services.downloader import download_audio
from app.services.transcriber import transcribe_to_srt
from app.services.rag_engine import RAGEngine

logger = logging.getLogger("audio_rag.pipeline")


def process_video(
    job_id: str,
    url: str,
    language: str,
    whisper_model: str,
    job_store: JobStore,
    rag: RAGEngine,
) -> None:
    """Complete pipeline executed as a background task."""
    try:
        job_store.update(job_id, status=JobStatus.DOWNLOADING)
        audio_path = download_audio(url, str(settings.audio_dir / job_id))

        job_store.update(job_id, status=JobStatus.TRANSCRIBING)
        srt_path = str(settings.srt_dir / f"{job_id}.srt")
        result = transcribe_to_srt(
            audio_path, srt_path, language=language, model_name=whisper_model,device="cpu"
        )

        job_store.update(job_id, status=JobStatus.INDEXING)
        rag.add_document(
            doc_id=job_id,
            text=result["text"],
            metadata={"source_url": url, "srt_path": srt_path},
        )

        job_store.update(
            job_id,
            status=JobStatus.DONE,
            srt_path=srt_path,
            text_preview=result["text"][:300],
        )
        logger.info("Job %s completed successfully", job_id)

    except Exception as e:
        logger.exception("Job %s failed", job_id)
        job_store.set_error(job_id, str(e))