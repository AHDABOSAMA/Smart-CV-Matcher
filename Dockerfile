# ── Stage: runtime ───────────────────────────────────────────────────────────
FROM python:3.10-slim

# Prevents Python from writing .pyc files and buffers stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install OS-level dependencies needed by pdfplumber and chromadb
RUN apt-get update && apt-get install -y --no-install-recommends \
    libglib2.0-0 \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies first (layer-cached unless requirements.txt changes)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source code
COPY app/ ./app/

# Create directories that the app writes to at runtime
RUN mkdir -p /app/data/cvs /app/chroma_db

# Expose the port FastAPI will listen on
EXPOSE 8001

# Health check — Docker will restart the container if this fails
HEALTHCHECK --interval=60s --timeout=30s --start-period=60s --retries=3 \
    CMD python -c "import httpx; httpx.get('http://localhost:8000/health').raise_for_status()"

# Start the server
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--timeout-keep-alive", "300"]
