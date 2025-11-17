"""
Search API endpoint for semantic LAQ search.
"""

from fastapi import APIRouter, HTTPException

from app.models.schemas import SearchQuery, SearchResponse, SearchResult
from app.services.rag import RAGService, RAGError
from app.services.config import Config
from app.services.database import LAQDatabase
from app.services.embeddings import EmbeddingService

router = APIRouter()


@router.post("/", response_model=SearchResponse)
async def search_laqs(query: SearchQuery):
    """
    Perform semantic search on LAQ database.

    - Generates query embedding
    - Retrieves relevant LAQs
    - Returns ranked results with similarity scores
    """

    try:
        # Initialize services
        config = Config()
        database = LAQDatabase(config)
        embedding_service = EmbeddingService(config)
        rag_service = RAGService(config, database, embedding_service)

        # Perform search
        results = rag_service.search(
            query=query.query,
            top_k=query.top_k,
            apply_threshold=True
        )

        # Convert to response model
        search_results = [
            SearchResult(
                question=result['metadata']['question'],
                answer=result['metadata']['answer'],
                metadata=result['metadata'],
                similarity_score=result['similarity']
            )
            for result in results
        ]

        return SearchResponse(
            query=query.query,
            results=search_results,
            total_results=len(search_results)
        )

    except RAGError as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")
