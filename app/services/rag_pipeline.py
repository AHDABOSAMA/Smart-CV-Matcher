"""
RAG Pipeline Service
─────────────────────
Orchestrates the full Retrieval-Augmented Generation loop:
  1. Embed the user query
  2. Retrieve top-k similar chunks from ChromaDB
  3. Build a structured prompt (context injection)
  4. Call the LLM via the Factory
  5. Return the answer + retrieved chunks for transparency
"""

import logging
from typing import Optional, List, Dict, Any

from app.services.vector_store import search, collection_count
from app.services.llm_factory import get_llm
from app.core.config import settings

logger = logging.getLogger(__name__)

# ── Prompt templates ──────────────────────────────────────────────────────────

SYSTEM_PROMPT = """You are an expert HR assistant and CV analyst.
You answer questions about candidates based ONLY on the CV excerpts provided below.
If the answer is not found in the excerpts, say "I could not find this information in the provided CV."
Never hallucinate skills or experience that are not explicitly mentioned.
Be concise, professional, and structured in your response.
If the CV content is in Arabic, respond in Arabic. Otherwise respond in English."""

CONTEXT_TEMPLATE = """
=== RETRIEVED CV EXCERPTS ===
{context}

=== USER QUESTION ===
{question}

Answer based only on the excerpts above:"""


def build_context(chunks: List[Dict[str, Any]]) -> str:
    """Format retrieved chunks into a readable context block."""
    parts = []
    for i, chunk in enumerate(chunks, start=1):
        parts.append(
            f"[Excerpt {i} | Source: {chunk['source']} | Relevance: {chunk['score']:.2f}]\n"
            f"{chunk['text']}"
        )
    return "\n\n---\n\n".join(parts)


def run_rag_pipeline(
    question: str,
    cv_filename: Optional[str] = None,
    top_k: Optional[int] = None,
    llm_provider: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Full RAG pipeline. Returns a dict matching QueryResponse schema.
    """
    effective_k = top_k or settings.TOP_K
    total_in_db = collection_count()

    if total_in_db == 0:
        return {
            "question":        question,
            "answer":          "No CVs have been uploaded yet. Please upload at least one CV first.",
            "llm_provider":    llm_provider or settings.LLM_PROVIDER,
            "retrieved_chunks": [],
            "total_chunks_searched": 0,
        }

    # ── Step 1: Retrieve ──────────────────────────────────────────────────────
    logger.info(f"Searching top-{effective_k} chunks for: '{question[:80]}…'")
    chunks = search(question, top_k=effective_k, source_filter=cv_filename)

    if not chunks:
        return {
            "question":        question,
            "answer":          "No relevant CV sections were found for your query.",
            "llm_provider":    llm_provider or settings.LLM_PROVIDER,
            "retrieved_chunks": [],
            "total_chunks_searched": total_in_db,
        }

    # ── Step 2: Build prompt ──────────────────────────────────────────────────
    context       = build_context(chunks)
    user_message  = CONTEXT_TEMPLATE.format(context=context, question=question)

    # ── Step 3: Generate ──────────────────────────────────────────────────────
    provider = llm_provider or settings.LLM_PROVIDER
    llm      = get_llm(provider)

    logger.info(f"Calling LLM provider: {provider}")
    try:
        answer = llm.generate(SYSTEM_PROMPT, user_message)
    except Exception as e:
        logger.error(f"LLM call failed: {e}")
        answer = f"LLM Error: {str(e)}"

    # ── Step 4: Return structured result ──────────────────────────────────────
    return {
        "question":     question,
        "answer":       answer,
        "llm_provider": provider,
        "retrieved_chunks": [
            {
                "text":     c["text"],
                "source":   c["source"],
                "chunk_id": c.get("chunk_id", ""),
                "score":    c["score"],
            }
            for c in chunks
        ],
        "total_chunks_searched": total_in_db,
    }
