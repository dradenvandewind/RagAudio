import os
from typing import Optional

import redis.asyncio as redis

from app.models.job import Job, JobStatus

# TTL par défaut des jobs dans Redis (en secondes). None = pas d'expiration.
JOB_TTL_SECONDS = int(os.getenv("JOB_TTL_SECONDS", "86400"))  # 24h par défaut


class JobStore:
    """Abstraction of job storage, backed by Redis.

    This class provides methods to create, retrieve, update, and delete job records in Redis.
    """

    def __init__(self, redis_url: Optional[str] = None) -> None:
        redis_url = redis_url or os.getenv("REDIS_URL", "redis://redis:6379/0")
        self._r = redis.Redis.from_url(redis_url, decode_responses=True)

    @staticmethod
    def _key(job_id: str) -> str:
        return f"job:{job_id}"

    async def create(self, job_id: str, url: str) -> Job:
        job = Job(job_id=job_id, url=url)
        await self._save(job)
        return job

    async def get(self, job_id: str) -> Optional[Job]:
        raw = await self._r.get(self._key(job_id))
        if raw is None:
            return None
        return Job.model_validate_json(raw)

    async def update(self, job_id: str, **fields) -> None:
        job = await self.get(job_id)
        if job:
            job.touch(**fields)
            await self._save(job)

    async def set_error(self, job_id: str, error: str) -> None:
        await self.update(job_id, status=JobStatus.ERROR, error=error)

    async def _save(self, job: Job) -> None:
        await self._r.set(
            self._key(job.job_id),
            job.model_dump_json(),
            ex=JOB_TTL_SECONDS,
        )


job_store = JobStore()