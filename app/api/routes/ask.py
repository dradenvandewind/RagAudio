from fastapi import APIRouter, Depends
from app.schemas import AskRequest, AskResponse
from app.services.rag_engine import RAGEngine
from app.api.deps import get_rag_engine

router = APIRouter(tags=["ask"])


@router.post("/ask", response_model=AskResponse)
def ask(req: AskRequest, rag: RAGEngine = Depends(get_rag_engine)):
    answer, sources = rag.query(req.question, top_k=req.top_k)
    return AskResponse(answer=answer, sources=sources)