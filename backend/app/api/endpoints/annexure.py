"""Annexure upload API endpoint for Excel files."""

import shutil
from pathlib import Path

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from app.models.schemas import AnnexureUploadResponse
from app.services.config import Config
from app.services.database import DatabaseError, LAQDatabase
from app.services.embeddings import EmbeddingError, EmbeddingService
from app.services.excel_processor import ExcelProcessingError, ExcelProcessor

router = APIRouter()


@router.post("/upload", response_model=AnnexureUploadResponse)
async def upload_annexure(
    file: UploadFile = File(...),
    laq_number: str = Form(...),
    pdf_name: str = Form(...),
    annexure_label: str = Form(None),
) -> AnnexureUploadResponse:
    """
    Upload and process an annexure Excel file (.xls/.xlsx) for a specific LAQ.

    - Validates file type
    - Parses Excel into readable text per sheet
    - Generates embedding and stores as annexure document
    - Links to LAQ via metadata (laq_number)
    """

    # Validate file type by extension first
    if not (file.filename.endswith(".xls") or file.filename.endswith(".xlsx")):
        raise HTTPException(status_code=400, detail="Only .xls/.xlsx files are allowed")

    upload_dir = Path("./uploads/annexures")
    upload_dir.mkdir(parents=True, exist_ok=True)
    file_path = upload_dir / file.filename

    try:
        with file_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to save annexure: {str(e)}"
        )

    try:
        config = Config()
        processor = ExcelProcessor()
        embeddings = EmbeddingService(config)
        db = LAQDatabase(config)

        annexure = processor.process_excel(str(file_path))

        # Use full text for storage/display; use truncated text for embedding generation
        full_text = annexure.to_text(max_chars=None)
        embed_text = full_text[: config.markdown_chunk_size]
        embedding = embeddings.embed_text(embed_text)

        stored_id = db.store_annexure(
            laq_num=laq_number,
            pdf_name=pdf_name,
            annexure_label=annexure_label or Path(file.filename).stem,
            content_text=full_text,
            embedding=embedding,
            extra_meta={
                "annexure_file": file.filename,
                "sheet_count": len(annexure.sheets),
            },
        )

        return AnnexureUploadResponse(
            success=True,
            message=f"Annexure stored with ID {stored_id}",
            laq_number=laq_number,
            annexure_label=annexure_label or Path(file.filename).stem,
            stored_id=stored_id,
        )

    except (ExcelProcessingError, EmbeddingError, DatabaseError) as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        try:
            if file_path.exists():
                file_path.unlink()
        except PermissionError:
            # Windows file lock – safe to ignore or log
            pass
