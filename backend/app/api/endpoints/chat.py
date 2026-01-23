"""
Chat API endpoint for conversational LAQ queries.
"""

import json
from pathlib import Path

from fastapi import APIRouter, HTTPException

from app.models.schemas import ChatQuery, ChatResponse, SearchResult
from app.services.config import Config
from app.services.database import LAQDatabase
from app.services.embeddings import EmbeddingService
from app.services.rag import RAGError, RAGService

router = APIRouter()


@router.post("/", response_model=ChatResponse)
async def chat_with_laqs(query: ChatQuery) -> ChatResponse:
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

        # Convert sources to response model with file URLs
        sources = []
        for source in source_results:
            metadata = source["metadata"]
            laq_number = metadata.get("laq_number", "")
            
            # Build reply document URL
            reply_document_url = None
            reply_doc_path = metadata.get("reply_document_path", "")
            if reply_doc_path and laq_number:
                filename = Path(reply_doc_path).name
                reply_document_url = f"/api/files/{laq_number}/{filename}"
            
            # Build attachment URLs
            attachment_urls = []
            attachment_paths_json = metadata.get("attachment_paths", "[]")
            try:
                attachment_paths = json.loads(attachment_paths_json) if isinstance(attachment_paths_json, str) else attachment_paths_json
                for att_path in attachment_paths:
                    if att_path and laq_number:
                        filename = Path(att_path).name
                        attachment_urls.append(f"/api/files/{laq_number}/{filename}")
            except:
                pass
            
            sources.append(SearchResult(
                question=metadata["question"],
                answer=metadata["answer"],
                metadata=metadata,
                similarity_score=source["similarity"],
                reply_document_url=reply_document_url,
                attachment_urls=attachment_urls
            ))

        return ChatResponse(question=query.question, answer=answer, sources=sources)

    except RAGError as e:
        raise HTTPException(status_code=500, detail=f"Chat failed: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")
