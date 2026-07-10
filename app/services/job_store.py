from typing import Optional
from app.models.job import Job, JobStatus


class JobStore:
    """Abstraction du stockage des jobs.
    Remplacer l'implémentation interne (dict) par Redis/Postgres
    sans toucher au reste du code : seule cette classe change.
    """

    def __init__(self) -> None:
        self._jobs: dict[str, Job] = {}

    def create(self, job_id: str, url: str) -> Job:
        job = Job(job_id=job_id, url=url)
        self._jobs[job_id] = job
        return job

    def get(self, job_id: str) -> Optional[Job]:
        return self._jobs.get(job_id)

    def update(self, job_id: str, **fields) -> None:
        job = self._jobs.get(job_id)
        if job:
            job.touch(**fields)

    def set_error(self, job_id: str, error: str) -> None:
        self.update(job_id, status=JobStatus.ERROR, error=error)


job_store = JobStore()