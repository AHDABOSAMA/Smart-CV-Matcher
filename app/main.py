"""
Smart CV Matcher - Main FastAPI Application
Entry point for the RAG-powered CV analysis system.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import cv_router, query_router, health_router
from app.core.config import settings

app = FastAPI(
    title="Smart CV Matcher",
    description="A RAG-powered system to analyze and match CVs to job requirements (English + Arabic)",
    version="1.0.0",
)

# Allow all origins for dev; restrict in production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register route groups
app.include_router(health_router, tags=["Health"])
app.include_router(cv_router,    prefix="/cv",    tags=["CV Management"])
app.include_router(query_router, prefix="/query", tags=["RAG Query"])


@app.get("/")
def root():
    return {
        "message": "Smart CV Matcher API is running 🚀",
        "docs": "/docs",
        "health": "/health",
    }
