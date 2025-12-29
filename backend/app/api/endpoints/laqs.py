"""LAQs listing endpoint for Dashboard."""

from typing import List

from fastapi import APIRouter, HTTPException

from app.services.config import Config
from app.services.database import DatabaseError, LAQDatabase

router = APIRouter()


@router.get("/", summary="List all LAQs")
async def list_all_laqs() -> List[dict]:
    """List all LAQ documents from the database.

    Returns a list of LAQ objects with metadata for Dashboard display.
    """
    try:
        config = Config()
        db = LAQDatabase(config)

        # Get all non-annexure documents
        results = db.collection.get(
            where={"type": {"$ne": "annexure"}}, include=["metadatas"]
        )

        metadatas = results.get("metadatas", [])

        # Transform to Dashboard-compatible format
        laqs = []
        seen_laq_nums = set()

        for meta in metadatas:
            laq_num = meta.get("laq_num", "N/A")

            # Only include each LAQ number once (skip duplicate Q&A pairs)
            if laq_num in seen_laq_nums:
                continue
            seen_laq_nums.add(laq_num)

            # Extract year from date if available
            date_str = meta.get("date", "")
            year = ""
            if date_str:
                # Try to extract year from date string (e.g., "2024-03-15" -> "2024")
                try:
                    if "-" in date_str:
                        year = date_str.split("-")[0]
                    elif "/" in date_str:
                        parts = date_str.split("/")
                        year = parts[2] if len(parts) == 3 else ""
                except Exception:
                    year = ""

            # Map backend metadata to Dashboard expected fields
            laq = {
                "laq_no": laq_num,
                "year": year or "N/A",
                "mla_name": meta.get("tabled_by", "N/A"),
                "department": meta.get("minister", "N/A"),
                "demand_no": "N/A",  # Not stored in current schema
                "type": meta.get("type", "N/A"),
                "cutmotion": "N/A",  # Not stored in current schema
                "duplicate": False,  # Not tracked in current schema
                "date": date_str or "N/A",
                "question": meta.get("question", "N/A"),
            }

            laqs.append(laq)

        return laqs

    except DatabaseError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {e}")
