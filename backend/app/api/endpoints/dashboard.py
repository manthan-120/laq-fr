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

        laqs = []

        for idx, meta in enumerate(documents["metadatas"]):
            laqs.append({
                "type": meta.get("type", "N/A"),
                "laq_number": meta.get("laq_number",),
                "mla_name": meta.get("mla_name", "N/A"),
                "year": meta.get("date", "").split("-")[-1],
                "minister": meta.get("minister", "N/A"),
                "department": meta.get("department", "N/A"),
                "demand_no": meta.get("demand_no", "N/A"),
                "cutmotion": meta.get("cutmotion",),
                "duplicate": meta.get("duplicate", False),
                "date": meta.get("date", "N/A"),
                "question": meta.get("question")
            })

        return laqs

    except DatabaseError as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")