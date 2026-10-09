"""
Pydantic models — define the shape of every request and response.
FastAPI uses these for automatic validation + OpenAPI docs.
"""

from pydantic import BaseModel, Field
from typing import Optional, List


# ── CV ingestion ──────────────────────────────────────────────────────────────

class CVUploadResponse(BaseModel):
    filename:    str
    chunks_added: int
    language_detected: str
    message:     str


# ── RAG query ─────────────────────────────────────────────────────────────────

class QueryRequest(BaseModel):
    question: str = Field(
        ...,
        json_schema_extra={
            "example": "Is this candidate suitable for a Data Analyst role?"
        },
        description="Natural-language question about the CVs (English or Arabic).",
    )
    cv_filename: Optional[str] = Field(
        None,
        json_schema_extra={"example": "john_doe.pdf"},
        description="Filter retrieval to a specific CV. Leave empty to search all CVs.",
    )
    top_k: Optional[int] = Field(
        None,
        ge=1, le=20,
        description="How many chunks to retrieve. Defaults to server setting.",
    )
    llm_provider: Optional[str] = Field(
        None,
        pattern="^(gemini|openai|ollama)$",
        examples=["gemini"],
        description="Override the default LLM provider for this request.",
    )


class RetrievedChunk(BaseModel):
    text:       str
    source:     str   # filename
    chunk_id:   str
    score:      float


class QueryResponse(BaseModel):
    question:        str
    answer:          str
    llm_provider:    str
    retrieved_chunks: List[RetrievedChunk]
    total_chunks_searched: int


# ── Health ────────────────────────────────────────────────────────────────────

class HealthResponse(BaseModel):
    status:       str
    llm_provider: str
    chroma_docs:  int
    embedding_model: str
