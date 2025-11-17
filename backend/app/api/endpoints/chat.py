"""
Chat API endpoint for conversational LAQ queries.
"""

from fastapi import APIRouter, HTTPException

from app.models.schemas import ChatQuery, ChatResponse, SearchResult
from app.services.rag import RAGService, RAGError
from app.services.config import Config
from app.services.database import LAQDatabase
from app.services.embeddings import EmbeddingService

router = APIRouter()


@router.post("/", response_model=ChatResponse)
async def chat_with_laqs(query: ChatQuery):
    """
    Chat with LAQ knowledge base.

    - Retrieves relevant LAQs
    - Generates contextual answer using LLM
    - Returns answer with source citations
    """

    try:
        # Initialize services
        config = Config()
        database = LAQDatabase(config)
        embedding_service = EmbeddingService(config)
        rag_service = RAGService(config, database, embedding_service)

        # Perform chat
        answer, source_results = rag_service.chat(
            query=query.question,
            top_k=query.top_k
        )

        # Convert sources to response model
        sources = [
            SearchResult(
                question=source['metadata']['question'],
                answer=source['metadata']['answer'],
                metadata=source['metadata'],
                similarity_score=source['similarity']
            )
            for source in source_results
        ]

        return ChatResponse(
            question=query.question,
            answer=answer,
            sources=sources
        )

    except RAGError as e:
        raise HTTPException(status_code=500, detail=f"Chat failed: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")
