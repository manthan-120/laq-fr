"""
Cleanup API endpoints for database maintenance.
"""

from fastapi import APIRouter, HTTPException

from app.services.config import Config
from app.services.database import DatabaseError, LAQDatabase

router = APIRouter()


@router.post("/remove-duplicate-annexures")
async def remove_duplicate_annexures():
    """
    Remove duplicate annexures from the database.
    
    Keeps only one copy of each LAQ + annexure label combination.
    Returns information about what was deleted.
    """
    try:
        config = Config()
        db = LAQDatabase(config)
        
        result = db.remove_duplicate_annexures()
        
        return {
            "success": True,
            "message": f"Removed {result['duplicates_found']} duplicate annexure(s)",
            "details": result
        }
        
    except DatabaseError as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")
