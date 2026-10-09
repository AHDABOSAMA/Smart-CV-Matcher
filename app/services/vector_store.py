"""
Vector Store Service
─────────────────────
Wraps ChromaDB. Handles:
  • Embedding CV chunks via sentence-transformers (free, local, multilingual)
  • Upserting chunks into the persistent collection
  • Semantic similarity search with optional source filtering
"""

import logging
from typing import List, Dict, Any, Optional

import chromadb
from chromadb.config import Settings as ChromaSettings
from sentence_transformers import SentenceTransformer

from app.core.config import settings

logger = logging.getLogger(__name__)

# ── Singletons (loaded once, reused across requests) ──────────────────────────
_chroma_client: Optional[chromadb.ClientAPI] = None
_collection = None
_embedder: Optional[SentenceTransformer] = None


def _get_embedder() -> SentenceTransformer:
    global _embedder
    if _embedder is None:
        logger.info(f"Loading embedding model: {settings.EMBEDDING_MODEL}")
        _embedder = SentenceTransformer(settings.EMBEDDING_MODEL)
    return _embedder


def _get_collection():
    global _chroma_client, _collection
    if _collection is None:
        _chroma_client = chromadb.PersistentClient(
            path=settings.CHROMA_PERSIST_DIR,
            settings=ChromaSettings(anonymized_telemetry=False),
        )
        _collection = _chroma_client.get_or_create_collection(
            name=settings.CHROMA_COLLECTION,
            metadata={"hnsw:space": "cosine"},   # cosine similarity for semantic search
        )
        logger.info(f"ChromaDB collection '{settings.CHROMA_COLLECTION}' ready.")
    return _collection


# ── Public API ────────────────────────────────────────────────────────────────

def embed_and_store(chunks: List[Dict[str, Any]]) -> int:
    """
    Embed a list of chunk dicts and upsert them into ChromaDB.
    Returns the number of chunks stored.
    """
    if not chunks:
        return 0

    collection = _get_collection()
    embedder   = _get_embedder()

    texts    = [c["text"]   for c in chunks]
    ids      = [c["id"]     for c in chunks]
    metadatas = [
        {
            "source":   c["source"],
            "page":     c["page"],
            "language": c["language"],
        }
        for c in chunks
    ]

    logger.info(f"Embedding {len(texts)} chunks …")
    embeddings = embedder.encode(texts, show_progress_bar=False).tolist()

    # Upsert = insert or update — safe to call multiple times with same PDF
    collection.upsert(
        ids=ids,
        embeddings=embeddings,
        documents=texts,
        metadatas=metadatas,
    )
    logger.info(f"Stored {len(chunks)} chunks in ChromaDB.")
    return len(chunks)


def search(
    query: str,
    top_k: int = 5,
    source_filter: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Embed the query and retrieve the top-k most similar chunks.
    Optionally filter by source filename.
    """
    collection = _get_collection()
    embedder   = _get_embedder()

    query_embedding = embedder.encode([query], show_progress_bar=False).tolist()

    where_clause = {"source": source_filter} if source_filter else None

    results = collection.query(
        query_embeddings=query_embedding,
        n_results=min(top_k, collection.count() or 1),
        where=where_clause,
        include=["documents", "metadatas", "distances"],
    )

    hits = []
    docs      = results["documents"][0]
    metas     = results["metadatas"][0]
    distances = results["distances"][0]

    for doc, meta, dist in zip(docs, metas, distances):
        hits.append({
            "text":     doc,
            "source":   meta.get("source", "unknown"),
            "chunk_id": "",          # not returned by query; set to empty
            "score":    round(1 - dist, 4),   # convert cosine distance → similarity
        })

    return hits


def collection_count() -> int:
    """Return total number of chunks currently stored."""
    try:
        return _get_collection().count()
    except Exception:
        return 0


def delete_by_source(filename: str) -> None:
    """Remove all chunks that belong to a given CV file."""
    collection = _get_collection()
    collection.delete(where={"source": filename})
    logger.info(f"Deleted all chunks for source: {filename}")
