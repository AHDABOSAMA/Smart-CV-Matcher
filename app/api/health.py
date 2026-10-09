from fastapi import APIRouter
from app.models import HealthResponse
from app.services.vector_store import collection_count
from app.core.config import settings

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
def health_check():
    """
    Returns system status — useful for Docker health checks and debugging.
    """
    return HealthResponse(
        status="ok",
        llm_provider=settings.LLM_PROVIDER,
        chroma_docs=collection_count(),
        embedding_model=settings.EMBEDDING_MODEL,
    )
