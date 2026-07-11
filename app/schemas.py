from dataclasses import Field
from typing import Optional, List
from pydantic import BaseModel, HttpUrl
from dataclasses import field as Field

class IngestRequest(BaseModel):
    #url: HttpUrl
    url: HttpUrl = Field(
        ...,
        description="URL de la vidéo à ingérer",
        examples=["https://www.dailymotion.com/player/metadata/video/x123abc"],
    )
    language: str = "fr"
    whisper_model: str = "small"  # tiny, base, small, medium, large-v3


class IngestResponse(BaseModel):
    job_id: str
    status: str


class JobStatus(BaseModel):
    job_id: str
    status: str
    url: Optional[str] = None
    srt_path: Optional[str] = None
    text_preview: Optional[str] = None
    error: Optional[str] = None


class AskRequest(BaseModel):
    question: str
    top_k: int = 4


class AskResponse(BaseModel):
    answer: str
    sources: List[str]
