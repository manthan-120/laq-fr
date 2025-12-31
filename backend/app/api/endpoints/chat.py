"""
Chat API endpoint for conversational LAQ queries.
"""

import json

from fastapi import APIRouter, HTTPException

from app.models.schemas import ChatQuery, ChatResponse, SearchResult
from app.services.config import Config
from app.services.database import DatabaseError, LAQDatabase
from app.services.embeddings import EmbeddingService
from app.services.rag import RAGError, RAGService

router = APIRouter()


def _normalize_label(label: str) -> str:
    """Normalize annexure label for comparison."""
    if not label:
        return ""
    import re
    label = label.upper().strip()
    label = re.sub(r"^ANNEX(?:URE)?S?[-\s]*", "", label)
    label = re.sub(r"^ANEXURES?[-\s]*", "", label)
    match = re.search(r"([IVivXLCDM]+)", label)
    if match:
        return match.group(1).upper()
    return label


@router.post("/", response_model=ChatResponse)
async def chat_with_laqs(query: ChatQuery) -> ChatResponse:
    """
    Chat with LAQ knowledge base.

    - Retrieves relevant LAQs
    - Generates contextual answer using LLM
    - Returns answer with source citations
    - Includes associated annexures for each source LAQ
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

        # Convert sources to response model and fetch annexures
        sources = []
        
        # Only process the top/most relevant source (the one being asked about)
        if source_results:
            source = source_results[0]  # Get only the most relevant LAQ
            
            # Extract referenced annexures from the source
            annexures = []
            metadata = source["metadata"]
            laq_num = metadata.get("laq_num")
            
            # Get referenced annexure labels
            referenced_annexures_str = metadata.get("referenced_annexures", "[]")
            try:
                referenced_annexures = json.loads(referenced_annexures_str)
                if referenced_annexures and laq_num:
                    # Normalize referenced annexures for comparison
                    normalized_refs = [_normalize_label(ref) for ref in referenced_annexures]
                    
                    # Fetch the actual annexure documents for this specific LAQ
                    try:
                        annexure_docs = database.get_annexures_for_laq(laq_num)
                        for idx, annexure_meta in enumerate(annexure_docs.get("metadatas", [])):
                            label = annexure_meta.get("annexure_label", "")
                            normalized_label = _normalize_label(label)
                            
                            if normalized_label in normalized_refs:
                                # Find the corresponding document content
                                doc_content = annexure_docs.get("documents", [])[idx] if idx < len(annexure_docs.get("documents", [])) else ""
                                annexures.append({
                                    "label": label,
                                    "content": doc_content,
                                    "metadata": annexure_meta
                                })
                    except DatabaseError:
                        # If annexure fetch fails, continue without it
                        pass
            except (json.JSONDecodeError, TypeError):
                pass
            
            sources.append(
                SearchResult(
                    question=metadata.get("question"),
                    answer=metadata.get("answer"),
                    metadata=metadata,
                    similarity_score=source["similarity"],
                    annexures=annexures
                )
            )

        return ChatResponse(question=query.question, answer=answer, sources=sources)

    except RAGError as e:
        raise HTTPException(status_code=500, detail=f"Chat failed: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")
