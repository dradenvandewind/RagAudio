from enum import StrEnum
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field


class JobStatus(StrEnum):
    QUEUED = "queued"
    DOWNLOADING = "downloading"
    TRANSCRIBING = "transcribing"
    INDEXING = "indexing"
    DONE = "done"
    ERROR = "error"


class Job(BaseModel):
    job_id: str
    url: str
    status: JobStatus = JobStatus.QUEUED
    srt_path: Optional[str] = None
    text_preview: Optional[str] = None
    error: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    def touch(self, **updates) -> None:
        for k, v in updates.items():
            setattr(self, k, v)
        self.updated_at = datetime.utcnow()