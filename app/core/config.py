"""
Core configuration — reads from environment variables (or .env via docker-compose).
All secrets/keys live here; never hardcode them elsewhere.
"""

import os
from functools import lru_cache


class Settings:
    # ── LLM provider selection ───────────────────────────────────────────────
    # Options: "gemini" | "openai" | "ollama"
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "ollama")

    # ── API keys (only the active provider needs to be set) ──────────────────
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    CORS_ORIGINS: str = os.getenv(
    "CORS_ORIGINS",
    "http://localhost:3000,http://localhost:8001",
    )


    # ── Ollama settings ───────────────────────────────────────────────────────
    OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "llama3")

    OLLAMA_BASE_URL: str = os.getenv(
        "OLLAMA_BASE_URL",
        "http://localhost:11434"
    )

    # ── Embedding model (free, multilingual: Arabic + English) ───────────────
    EMBEDDING_MODEL: str = os.getenv(
        "EMBEDDING_MODEL",
        "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
    )

    # ── ChromaDB ──────────────────────────────────────────────────────────────
    CHROMA_PERSIST_DIR: str = os.getenv("CHROMA_PERSIST_DIR", "./chroma_db")
    CHROMA_COLLECTION: str = os.getenv("CHROMA_COLLECTION", "cv_chunks")

    # ── Chunking strategy ─────────────────────────────────────────────────────
    CHUNK_SIZE: int = int(os.getenv("CHUNK_SIZE", "400"))
    CHUNK_OVERLAP: int = int(os.getenv("CHUNK_OVERLAP", "50"))
    
    # ── Retrieval ──────────────────────────────────────────────────────────────
    TOP_K: int = int(os.getenv("TOP_K", "5"))



@lru_cache()
def get_settings() -> Settings:
    config = Settings()

    if config.CHUNK_SIZE <= 0:
        raise ValueError("CHUNK_SIZE must be greater than 0.")

    if (
        config.CHUNK_OVERLAP < 0
        or config.CHUNK_OVERLAP >= config.CHUNK_SIZE
    ):
        raise ValueError(
            "CHUNK_OVERLAP must be non-negative and smaller than CHUNK_SIZE."
        )

    if config.TOP_K <= 0:
        raise ValueError("TOP_K must be greater than 0.")

    return config



settings = get_settings()
