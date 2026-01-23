"""
File serving endpoint for LAQ documents and annexures.
"""

from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

router = APIRouter()


@router.get("/{laq_number}/{filename}")
async def serve_file(laq_number: str, filename: str):
    """
    Serve reply documents and annexure files.
    
    Files are stored in ./uploads/{laq_number}/{filename}
    """
    
    # Construct file path
    file_path = Path(f"./uploads/{laq_number}/{filename}")
    
    # Security: Ensure the path is within uploads directory (prevent directory traversal)
    try:
        file_path = file_path.resolve()
        uploads_dir = Path("./uploads").resolve()
        
        if not str(file_path).startswith(str(uploads_dir)):
            raise HTTPException(status_code=403, detail="Access denied")
    except Exception:
        raise HTTPException(status_code=403, detail="Invalid file path")
    
    # Check if file exists
    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(status_code=404, detail="File not found")
    
    # Determine media type based on extension
    extension = file_path.suffix.lower()
    media_type_map = {
        '.pdf': 'application/pdf',
        '.doc': 'application/msword',
        '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        '.xls': 'application/vnd.ms-excel',
        '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        '.txt': 'text/plain',
        '.md': 'text/markdown',
    }
    
    media_type = media_type_map.get(extension, 'application/octet-stream')
    
    # Return file
    return FileResponse(
        path=str(file_path),
        media_type=media_type,
        filename=filename
    )
