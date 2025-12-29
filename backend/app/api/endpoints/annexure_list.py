"""Annexure listing endpoint for debugging and UI consumption."""

from fastapi import APIRouter, HTTPException, Query

from app.services.config import Config
from app.services.database import LAQDatabase, DatabaseError

router = APIRouter()


@router.get("/", summary="List annexures for a LAQ")
async def list_annexures(laq_number: str = Query(..., alias="laq_number")):
    """List stored annexures for a given LAQ number.

    Returns metadata and full text so clients can verify availability.
    """
    try:
        config = Config()
        db = LAQDatabase(config)
        annexures = db.get_annexures_for_laq(laq_number)
        metadatas = annexures.get("metadatas", []) or []
        documents = annexures.get("documents", []) or []

        results = []
        for meta, doc in zip(metadatas, documents):
            results.append(
                {
                    "annexure_label": meta.get("annexure_label"),
                    "pdf": meta.get("pdf"),
                    "laq_num": meta.get("laq_num"),
                    "length": len(doc) if isinstance(doc, str) else 0,
                    "document": doc,
                }
            )

        return {"count": len(results), "annexures": results}
    except DatabaseError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {e}")
