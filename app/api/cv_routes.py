"""
CV Router — MVC Controller for CV management
"""

import os
import shutil
import logging
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks

from app.models import CVUploadResponse
from app.services.pdf_parser import parse_pdf_to_chunks
from app.services.vector_store import embed_and_store, delete_by_source, collection_count
from app.core.config import settings

router = APIRouter()
logger = logging.getLogger(__name__)

DATA_DIR = Path("./data/cvs")
DATA_DIR.mkdir(parents=True, exist_ok=True)


@router.post("/upload", response_model=CVUploadResponse)
async def upload_cv(file: UploadFile = File(...)):
    """
    Upload a CV PDF. The file is:
      1. Saved to disk
      2. Parsed into chunks (custom logic)
      3. Embedded and stored in ChromaDB

    Accepts: .pdf files only
    """
        
    if not file.filename:
        raise HTTPException(status_code=400, detail="A filename is required.")

    original_filename = Path(file.filename.replace("\\", "/")).name

    if not original_filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are accepted.")

    stored_filename = f"{uuid4().hex}_{original_filename}"
    save_path = DATA_DIR / stored_filename


    # Save the uploaded PDF to disk
    try:
        with open(save_path, "wb") as f:
            shutil.copyfileobj(file.file, f)
        logger.info(f"Saved uploaded file to {save_path}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save file: {e}")

    # Parse PDF → chunks
    try:
        chunks, lang = parse_pdf_to_chunks(
            save_path,
            chunk_size=settings.CHUNK_SIZE,
            chunk_overlap=settings.CHUNK_OVERLAP,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF parsing failed: {e}")

    if not chunks:
        raise HTTPException(
            status_code=422,
            detail="No text could be extracted from this PDF. It may be a scanned image.",
        )

    # Embed + store in ChromaDB
    try:
        stored = embed_and_store(chunks)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Embedding/storage failed: {e}")

    return CVUploadResponse(
        filename=stored_filename,
        chunks_added=stored,
        language_detected=lang,
        message=f"Successfully processed '{original_filename}' into {stored} chunks.",
    )




@router.delete("/{filename}")
def delete_cv(filename: str):
    """
    Remove a CV's chunks from ChromaDB and delete its file from disk.
    """
    if (
        Path(filename.replace("\\", "/")).name != filename
        or "/" in filename
        or "\\" in filename
    ):
        raise HTTPException(status_code=400, detail="Invalid filename.")

    if not filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF filenames are accepted.")

    file_path = DATA_DIR / filename

    if not file_path.is_file():
        raise HTTPException(status_code=404, detail="CV not found.")

    delete_by_source(filename)
    file_path.unlink()

    return {
        "message": f"'{filename}' has been deleted.",
        "remaining_chunks": collection_count(),
    }


@router.get("/list")
def list_cvs():
    """List all PDF files currently stored."""
    files = [f.name for f in DATA_DIR.glob("*.pdf")]
    return {"cvs": files, "total_chunks_in_db": collection_count()}
