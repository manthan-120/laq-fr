"""
FastAPI application entry point for LAQ RAG system.
Provides REST API endpoints for PDF upload, search, and chat functionality.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.endpoints import upload, search, chat, database, annexure, annexure_list
from app.core.config import get_settings

settings = get_settings()

app = FastAPI(
    title="LAQ RAG API",
    description="Retrieval-Augmented Generation API for Legislative Assembly Questions",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# CORS middleware for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],  # React dev servers
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


@app.get("/")
async def root():
    """Root endpoint - health check."""
    return {
        "message": "LAQ RAG API is running",
        "version": "1.0.0",
        "docs": "/api/docs"
    }


@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "ollama_running": True,  # TODO: Add actual Ollama connection check
        "database": "connected"
    }
