from fastapi import Request
from app.services.job_store import JobStore
from app.services.rag_engine import RAGEngine


def get_job_store(request: Request) -> JobStore:
    return request.app.state.job_store


def get_rag_engine(request: Request) -> RAGEngine:
    return request.app.state.rag