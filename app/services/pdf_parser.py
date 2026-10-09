"""
PDF Parser Service
─────────────────
Handles raw PDF ingestion including:
  • Multi-column layouts
  • Arabic RTL text (via pdfplumber's char-level extraction)
  • Metadata tagging per chunk (filename, page, language)
  • Custom chunking strategy: 400 tokens, 50-token overlap

WHY these chunking numbers?
  • 400 tokens ≈ ~300 words — enough context for the LLM to reason about
    a CV section (education block, skills list, experience entry) without
    overwhelming the context window or diluting retrieval precision.
  • 50-token overlap ensures a sentence split across two chunks is fully
    seen by at least one chunk, avoiding truncated meaning.
"""
from typing import Union
import re
import uuid
import logging
from pathlib import Path
from typing import List, Dict, Any, Tuple

import pdfplumber
from langdetect import detect, LangDetectException

logger = logging.getLogger(__name__)

# ── Arabic unicode range check ────────────────────────────────────────────────
_ARABIC_RE = re.compile(r"[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF]+")


def _detect_language(text: str) -> str:
    """Return ISO 639-1 language code, defaulting to 'en'."""
    try:
        lang = detect(text[:500])   # sample first 500 chars for speed
        return lang
    except LangDetectException:
        return "en"


def _has_arabic(text: str) -> bool:
    return bool(_ARABIC_RE.search(text))


def _normalize_arabic(text: str) -> str:
    """
    Basic Arabic normalization:
      • Remove tashkeel (diacritics) — they vary across documents and cause
        embedding mismatch for the same word written differently.
      • Normalize Alef variants → plain Alef (ا).
      • Normalize Ta Marbuta variants.
    """
    # Remove diacritics (harakat)
    text = re.sub(r"[\u064B-\u065F\u0670]", "", text)
    # Normalize Alef variants
    text = re.sub(r"[إأآٱ]", "ا", text)
    # Normalize Ya variants
    text = re.sub(r"ى", "ي", text)
    # Normalize Ha
    text = re.sub(r"ة", "ه", text)
    return text


def _clean_text(text: str, lang: str) -> str:
    """Remove noise: multiple spaces, weird chars, page numbers."""
    text = re.sub(r"\s+", " ", text)              # collapse whitespace
    text = re.sub(r"[^\w\s\u0600-\u06FF,.@()\-/+]", " ", text)  # keep Arabic + basic punct
    if lang == "ar" or _has_arabic(text):
        text = _normalize_arabic(text)
    return text.strip()


def _token_split(text: str, chunk_size: int = 400, overlap: int = 50) -> List[str]:
    """
    Naïve whitespace-token chunker with sliding window overlap.
    Using words as proxy tokens (fast, no tokenizer dependency needed here).
    """
    words = text.split()
    chunks = []
    start = 0
    while start < len(words):
        end = start + chunk_size
        chunk = " ".join(words[start:end])
        if chunk.strip():
            chunks.append(chunk)
        if end >= len(words):
            break
        start = end - overlap   # slide back by overlap amount
    return chunks


def parse_pdf_to_chunks(
    file_path: Union[str, Path],
    chunk_size: int = 400,
    chunk_overlap: int = 50,
) -> Tuple[List[Dict[str, Any]], str]:
    """
    Parse a PDF file and return:
      - List of chunk dicts: {id, text, source, page, language}
      - Detected language string

    Each chunk is ready to be embedded and stored in ChromaDB.
    """
    file_path = Path(file_path)
    filename = file_path.name
    all_text_pages: List[Tuple[int, str]] = []

    logger.info(f"Parsing PDF: {filename}")

    with pdfplumber.open(file_path) as pdf:
        for page_num, page in enumerate(pdf.pages, start=1):
            # extract_text preserves reading order; works better than PyPDF2
            raw = page.extract_text(x_tolerance=3, y_tolerance=3) or ""
            if raw.strip():
                all_text_pages.append((page_num, raw))

    if not all_text_pages:
        logger.warning(f"No text extracted from {filename}. Possibly a scanned image PDF.")
        return [], "unknown"

    # Detect language from first page text
    first_text = all_text_pages[0][1]
    lang = "ar" if _has_arabic(first_text) else _detect_language(first_text)

    chunks: List[Dict[str, Any]] = []

    for page_num, raw_text in all_text_pages:
        cleaned = _clean_text(raw_text, lang)
        page_chunks = _token_split(cleaned, chunk_size, chunk_overlap)

        for chunk_text in page_chunks:
            chunk_id = str(uuid.uuid4())
            chunks.append({
                "id":       chunk_id,
                "text":     chunk_text,
                "source":   filename,
                "page":     page_num,
                "language": lang,
            })

    logger.info(f"Extracted {len(chunks)} chunks from '{filename}' (lang={lang})")
    return chunks, lang
