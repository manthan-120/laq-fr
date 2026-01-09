"""
Dashboard API endpoint for listing all LAQs.
Used by Dashboard.jsx
"""

from fastapi import APIRouter, HTTPException
from typing import List

from app.services.database import LAQDatabase, DatabaseError
from app.services.config import Config

router = APIRouter(prefix="/laqs", tags=["Dashboard"])


@router.get("/", response_model=List[dict])
async def get_all_laqs():
    """
    Return all LAQs for dashboard table and filters.
    No LLM required.
    """

    try:
        config = Config()
        db = LAQDatabase(config)

        collection = db.client.get_collection(config.collection_name)

        documents = collection.get(include=["metadatas", "documents"])

        # Normalize documents list from Chroma (may be nested)
        docs_raw = documents.get("documents", []) or []
        if docs_raw and isinstance(docs_raw, list) and isinstance(docs_raw[0], list):
            docs = docs_raw[0]
        else:
            docs = docs_raw

        laqs = []

        for idx, meta in enumerate(documents.get("metadatas", [])):
            # Extract year from date if available
            date_str = meta.get("date", "")
            year = ""
            if date_str:
                # Try to extract year from date string (e.g., "2024-03-15" -> "2024")
                try:
                    if "-" in date_str:
                        year = date_str.split("-")[-1]
                    elif "/" in date_str:
                        parts = date_str.split("/")
                        year = parts[2] if len(parts) == 3 else ""
                except Exception:
                    year = ""

            # Derive question: use stored document as primary source, then metadata
            question_text = ""
            doc_text = docs[idx] if idx < len(docs) else ""
            if isinstance(doc_text, str) and doc_text:
                try:
                    # if "Q:" in doc_text and "\nA:" in doc_text:
                    #     question_text = doc_text.split("Q:", 1)[1].split("\nA:", 1)[0].strip()
                    # else:
                        question_text = doc_text.strip()
                except Exception:
                    question_text = ""

            # if not question_text:
            #     question_text = (meta.get("question") or "").strip()

            laqs.append({
                "type": meta.get("type", "N/A"),
                "laq_number": meta.get("laq_number",),
                "mla_name": meta.get("mla_name", "N/A"),
                # "year": meta.get("date", "").split("-")[-1],
                "year": year or "N/A",
                "minister": meta.get("minister", "N/A"),
                # "department": meta.get("department", "N/A"),
                # "demand_no": meta.get("demand_no", "N/A"),
                "cutmotion": meta.get("cutmotion",),
                # "duplicate": meta.get("duplicate", False),
                # "date": meta.get("date", "N/A"),
                "date": date_str or "N/A",
                "question": question_text,
            })

        return laqs

    except DatabaseError as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")