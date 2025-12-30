"""
FastAPI application entry point for LAQ RAG system.
Provides REST API endpoints for PDF upload, search, and chat functionality.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.endpoints import (
    annexure,
    annexure_list,
    chat,
    database,
    laqs,
    search,
    upload,
    validation,
)
from app.core.config import get_settings

settings = get_settings()

app = FastAPI(
    title="LAQ RAG API",
    description="Retrieval-Augmented Generation API for Legislative Assembly Questions",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

# CORS middleware for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
    ],  # React dev servers
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(upload.router, prefix="/api/upload", tags=["upload"])
app.include_router(annexure.router, prefix="/api/annexure", tags=["annexure"])
app.include_router(annexure_list.router, prefix="/api/annexure", tags=["annexure"])
app.include_router(search.router, prefix="/api/search", tags=["search"])
app.include_router(chat.router, prefix="/api/chat", tags=["chat"])
app.include_router(database.router, prefix="/api/database", tags=["database"])
app.include_router(laqs.router, prefix="/api/laqs", tags=["laqs"])
app.include_router(validation.router, prefix="/api/validation", tags=["validation"])


@app.get("/")
async def root() -> dict:
    """Root endpoint - health check."""
    return {
        "message": "LAQ RAG API is running",
        "version": "1.0.0",
        "docs": "/api/docs",
    }


@app.get("/api/health")
async def health_check() -> dict:
    """Health check endpoint."""
    ollama_status = False
    db_status = False

    try:
        # Check Ollama connection
        import ollama

        ollama.list()
        ollama_status = True
    except Exception:
        ollama_status = False

    try:
        # Check database connection
        from app.services.database import LAQDatabase

        db = LAQDatabase(settings)
        db.get_count()  # Simple operation to verify connection
        db_status = True
    except Exception:
        db_status = False

    overall_status = "healthy" if (ollama_status and db_status) else "degraded"

    return {
        "status": overall_status,
        "ollama_running": ollama_status,
        "database": "connected" if db_status else "disconnected",
    }
