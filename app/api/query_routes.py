"""
Query Router — MVC Controller for RAG queries
"""

import logging
from fastapi import APIRouter, HTTPException

from app.models import QueryRequest, QueryResponse
from app.services.rag_pipeline import run_rag_pipeline

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/ask", response_model=QueryResponse)
def ask_question(request: QueryRequest):
    """
    Main RAG endpoint. Accepts a natural-language question and returns:
      - answer  : LLM-generated answer grounded in retrieved CV chunks
      - retrieved_chunks : the chunks used to form the answer (for transparency)
      - llm_provider : which LLM was used

    Example questions:
      - "Is this candidate suitable for a data analyst role?"
      - "What programming languages does John know?"
      - "ما هي مهارات المرشح؟"  (Arabic: What are the candidate's skills?)
    """
    try:
        result = run_rag_pipeline(
            question=request.question,
            cv_filename=request.cv_filename,
            top_k=request.top_k,
            llm_provider=request.llm_provider,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"RAG pipeline error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal error: {e}")

    return QueryResponse(**result)
