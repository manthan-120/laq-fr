"""
Upload API endpoint for PDF processing.
"""

from fastapi import APIRouter, UploadFile, File, HTTPException
from pathlib import Path
import shutil

from app.models.schemas import UploadResponse, LAQDataResponse, QAPairResponse
from app.services.pdf_processor import PDFProcessor, PDFProcessingError
from app.services.embeddings import EmbeddingService, EmbeddingError
from app.services.database import LAQDatabase, DatabaseError
from app.services.config import Config

router = APIRouter()


@router.post("/", response_model=UploadResponse)
async def upload_pdf(file: UploadFile = File(...)):
    """
    Upload and process a LAQ PDF file.

    - Validates PDF file
    - Extracts structured Q&A pairs
    - Generates embeddings
    - Stores in vector database
    """

    # Validate file type
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")

    # Create upload directory if not exists
    upload_dir = Path("./uploads")
    upload_dir.mkdir(exist_ok=True)

    # Save uploaded file temporarily
    file_path = upload_dir / file.filename
    try:
        with file_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")

    try:
        # Initialize services
        config = Config()
        pdf_processor = PDFProcessor(config)
        embedding_service = EmbeddingService(config)
        db = LAQDatabase(config)

        # Check if PDF already processed (if enabled)
        if config.skip_duplicate_pdfs:
            if db.pdf_already_processed(file.filename):
                existing_count = db.get_pdf_qa_count(file.filename)
                raise HTTPException(
                    status_code=409,
                    detail=f"PDF '{file.filename}' already processed with {existing_count} Q&A pairs. "
                           f"Delete existing entries first or disable SKIP_DUPLICATE_PDFS."
                )

        # Process PDF (with caching if enabled)
        laq_data = pdf_processor.process_pdf(str(file_path))

        # Prepare metadata for enhanced embeddings
        laq_metadata = {
            'laq_type': laq_data.laq_type,
            'minister': laq_data.minister,
            'date': laq_data.date,
            'pdf_title': laq_data.pdf_title
        }

        # Convert Q&A pairs to dict format
        qa_pairs_dict = [
            {'question': qa.question, 'answer': qa.answer}
            for qa in laq_data.qa_pairs
        ]

        # Generate embeddings with optimizations
        embeddings_list = embedding_service.embed_qa_pairs(
            qa_pairs=qa_pairs_dict,
            laq_metadata=laq_metadata if config.use_enhanced_context else None,
            use_enhanced_context=config.use_enhanced_context
        )

        # Store in database
        laq_data_dict = {
            'pdf_title': laq_data.pdf_title,
            'laq_type': laq_data.laq_type,
            'laq_number': laq_data.laq_number,
            'minister': laq_data.minister,
            'date': laq_data.date,
            'tabled_by': laq_data.tabled_by,
            'attachments': laq_data.attachments,
            'qa_pairs': qa_pairs_dict
        }

        stored_count = db.store_qa_pairs(
            laq_data=laq_data_dict,
            pdf_name=file.filename,
            embeddings_list=embeddings_list
        )

        # Convert to response model
        qa_pairs_response = [
            QAPairResponse(question=qa.question, answer=qa.answer)
            for qa in laq_data.qa_pairs
        ]

        laq_response = LAQDataResponse(
            pdf_title=laq_data.pdf_title,
            laq_type=laq_data.laq_type,
            laq_number=laq_data.laq_number,
            minister=laq_data.minister,
            date=laq_data.date,
            qa_pairs=qa_pairs_response,
            tabled_by=laq_data.tabled_by,
            attachments=laq_data.attachments
        )

        return UploadResponse(
            success=True,
            message=f"Successfully processed {file.filename} - Stored {stored_count} Q&A pairs",
            pdf_name=file.filename,
            qa_pairs_extracted=len(laq_data.qa_pairs),
            laq_data=laq_response
        )

    except PDFProcessingError as e:
        raise HTTPException(status_code=400, detail=f"PDF processing failed: {str(e)}")
    except EmbeddingError as e:
        raise HTTPException(status_code=500, detail=f"Embedding generation failed: {str(e)}")
    except DatabaseError as e:
        raise HTTPException(status_code=500, detail=f"Database operation failed: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")
    finally:
        # Clean up uploaded file
        if file_path.exists():
            file_path.unlink()
