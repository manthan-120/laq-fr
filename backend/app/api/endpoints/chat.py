"""
Chat API endpoint for conversational LAQ queries.
"""

from fastapi import APIRouter, HTTPException

from app.models.schemas import ChatQuery, ChatResponse, SearchResult
from app.services.config import Config
from app.services.database import LAQDatabase
from app.services.embeddings import EmbeddingService
from app.services.rag import RAGError, RAGService

router = APIRouter()


@router.post("/", response_model=None)
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
            query=query.question, top_k=query.top_k
        )

        # Convert sources to response model
        sources = [
            {
                "question": src.get("metadata", {}).get("question", "N/A"),
                "answer": src.get("metadata", {}).get("answer", "N/A"),
                "metadata": src.get("metadata", {}),
                "similarity_score": src.get("similarity", 0),
                "document": src.get("document"),   # include annex text if present
            }
            for src in source_results
        ]

        return {"question": query.question, "answer": answer, "sources": sources}

    except RAGError as e:
        raise HTTPException(status_code=500, detail=f"Chat failed: {str(e)}")
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

    except RAGError as e:
        raise HTTPException(status_code=500, detail=f"Chat failed: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")
