"""
Search API endpoint for semantic LAQ search.
"""

import json

from fastapi import APIRouter, HTTPException

from app.models.schemas import SearchQuery, SearchResponse, SearchResult
from app.services.config import Config
from app.services.database import DatabaseError, LAQDatabase
from app.services.embeddings import EmbeddingService
from app.services.rag import RAGError, RAGService
from app.services.validation import ValidationService

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


@router.post("/", response_model=SearchResponse)
async def search_laqs(query: SearchQuery) -> SearchResponse:
    """
    Perform semantic search on LAQ database.

    - Generates query embedding
    - Retrieves relevant LAQs
    - Returns ranked results with similarity scores
    - Includes associated annexures if referenced in the answer
    """

    try:
        # Initialize services
        config = Config()
        database = LAQDatabase(config)
        embedding_service = EmbeddingService(config)
        rag_service = RAGService(config, database, embedding_service)

        # Perform search
        results = rag_service.search(
            query=query.query, top_k=query.top_k, apply_threshold=True
        )

        # Convert to response model and fetch associated annexures
        search_results = []
        for result in results:
            # Extract referenced annexures from the result
            annexures = []
            metadata = result["metadata"]
            laq_num = metadata.get("laq_num")
            
            # Get referenced annexure labels
            referenced_annexures_str = metadata.get("referenced_annexures", "[]")
            try:
                referenced_annexures = json.loads(referenced_annexures_str)
                if referenced_annexures and laq_num:
                    # Normalize referenced annexures for comparison
                    normalized_refs = [_normalize_label(ref) for ref in referenced_annexures]
                    print(f"🔍 LAQ {laq_num}: referenced_annexures = {referenced_annexures}, normalized = {normalized_refs}")
                    
                    # Fetch the actual annexure documents
                    try:
                        annexure_docs = database.get_annexures_for_laq(laq_num)
                        print(f"  Found {len(annexure_docs.get('metadatas', []))} annexure(s) in DB for LAQ {laq_num}")
                        
                        for idx, annexure_meta in enumerate(annexure_docs.get("metadatas", [])):
                            label = annexure_meta.get("annexure_label", "")
                            normalized_label = _normalize_label(label)
                            print(f"    Annexure {idx}: label='{label}', normalized='{normalized_label}'")
                            
                            if normalized_label in normalized_refs:
                                # Find the corresponding document content
                                doc_content = annexure_docs.get("documents", [])[idx] if idx < len(annexure_docs.get("documents", [])) else ""
                                print(f"      ✓ MATCH! Adding to results (content length: {len(doc_content)})")
                                annexures.append({
                                    "label": label,
                                    "content": doc_content,
                                    "metadata": annexure_meta
                                })
                    except DatabaseError as e:
                        # If annexure fetch fails, continue without it
                        print(f"  ❌ Error fetching annexures: {e}")
            except (json.JSONDecodeError, TypeError) as e:
                print(f"  Error parsing referenced_annexures: {e}")
            
            search_results.append(
                SearchResult(
                    question=metadata.get("question", "N/A"),
                    answer=metadata.get("answer", "N/A"),
                    metadata=metadata,
                    similarity_score=result["similarity"],
                    annexures=annexures
                )
            )

        return SearchResponse(
            query=query.query, results=search_results, total_results=len(search_results)
        )

    except RAGError as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")
