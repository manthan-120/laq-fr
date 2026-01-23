"""
Upload API endpoint for PDF processing.
"""

import json
import re
import shutil
from pathlib import Path
from typing import List

from fastapi import APIRouter, File, HTTPException, UploadFile, Form

from app.models.schemas import (
    LAQDataResponse, 
    UploadResponse, 
    ProcessingResponse,
    ConfirmStoreRequest,
    ConfirmStoreResponse
)
from app.services.config import Config
from app.services.database import DatabaseError, LAQDatabase
from app.services.embeddings import EmbeddingError, EmbeddingService
from app.services.pdf_processor import PDFProcessingError, PDFProcessor

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
    # Allow PDF and Word documents
    allowed_exts = ('.pdf', '.doc', '.docx')
    if not file.filename.lower().endswith(allowed_exts):
        raise HTTPException(status_code=400, detail="Only PDF or Word files are allowed (.pdf, .doc, .docx)")

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

        # Extract LAQ number from filename for validation
        filename_laq_number = pdf_processor.extract_laq_number_from_filename(
            file.filename
        )
        if filename_laq_number:
            print(f"📋 Filename indicates LAQ number: {filename_laq_number}")

        # Check if PDF already processed (if enabled)
        if config.skip_duplicate_pdfs:
            if db.pdf_already_processed(file.filename):
                existing_count = db.get_pdf_qa_count(file.filename)
                raise HTTPException(
                    status_code=409,
                    detail=f"PDF '{file.filename}' already processed with {existing_count} Q&A pairs. "
                    f"Delete existing entries first or disable SKIP_DUPLICATE_PDFS.",
                )

        # Process PDF (with caching if enabled)
        laq_data = pdf_processor.process_pdf(str(file_path))

        # Prepare metadata for enhanced embeddings
        laq_metadata = {
            'pdf_title': laq_data.pdf_title,
            'laq_type': laq_data.laq_type,
            'laq_number': laq_data.laq_number,
            'mla_name': laq_data.mla_name,
            'date': laq_data.date,
            'minister': laq_data.minister,
        }

        # Convert Q&A pairs to dict format
        qa_pairs_dict = [
            {"question": qa.question, "answer": qa.answer, "attachments": qa.attachments} 
            for qa in laq_data.qa_pairs
        ]

        # Generate embeddings with optimizations
        embeddings_list = embedding_service.embed_qa_pairs(
            qa_pairs=qa_pairs_dict,
            laq_metadata=laq_metadata if config.use_enhanced_context else None,
            use_enhanced_context=config.use_enhanced_context,
        )

        # Store in database
        laq_data_dict = {
            'pdf_title': laq_data.pdf_title,
            'laq_type': laq_data.laq_type,
            'laq_number': laq_data.laq_number,
            'mla_name': laq_data.mla_name,
            'date': laq_data.date,
            'minister': laq_data.minister,
            'attachments': [],  # Empty list - attachments are at QA pair level
            'reply_document_path': str(file_path),  # Store the uploaded file path
            'qa_pairs': qa_pairs_dict
        }

        stored_count = db.store_qa_pairs(
            laq_data=laq_data_dict,
            pdf_name=file.filename,
            embeddings_list=embeddings_list,
        )

        return UploadResponse(
            success=True,
            message=f"Successfully processed {file.filename} - Stored {stored_count} Q&A pairs",
            pdf_name=file.filename,
            qa_pairs_extracted=len(laq_data.qa_pairs),
            laq_data=laq_data,
        )

    except PDFProcessingError as e:
        raise HTTPException(status_code=400, detail=f"PDF processing failed: {str(e)}")
    except EmbeddingError as e:
        raise HTTPException(
            status_code=500, detail=f"Embedding generation failed: {str(e)}"
        )
    except DatabaseError as e:
        raise HTTPException(
            status_code=500, detail=f"Database operation failed: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")
    finally:
        # Clean up uploaded file
        if file_path.exists():
            file_path.unlink()


def _extract_annexure_label_from_filename(filename: str) -> str:
    """Extract annexure label from filename (e.g., 'Annexure_A.xlsx' -> 'A')."""
    match = re.search(r'annexure[_\s-]*([a-zA-Z0-9]+)', filename, re.IGNORECASE)
    if match:
        return match.group(1).upper()
    return ""


def _auto_link_annexures(qa_pairs: list, available_annexures: list) -> list:
    """Auto-link annexures to Q&A pairs based on references in answers."""
    annexure_labels = {_extract_annexure_label_from_filename(ann): ann for ann in available_annexures}
    
    for qa in qa_pairs:
        answer = qa.get("answer", "")
        # Find annexure references (e.g., "Annexure A", "ANNEXURE-B", etc.)
        referenced = set()
        for match in re.finditer(r'annexure[_\s-]*([a-zA-Z0-9]+)', answer, re.IGNORECASE):
            label = match.group(1).upper()
            if label in annexure_labels:
                referenced.add(annexure_labels[label])
        
        if referenced:
            qa["attachments"] = list(referenced)
    
    return qa_pairs


@router.post("/process", response_model=ProcessingResponse)
async def process_laq_for_validation(
    reply_file: UploadFile = File(...),
    annexure_files: List[UploadFile] = File(default=[])
):
    """
    Process LAQ reply document and annexures for validation.
    
    Step 1: Upload files and extract data
    - Saves reply document and annexure files to ./uploads/{laq_number}/
    - Processes reply document to extract LAQ data
    - Auto-links annexures to Q&A pairs
    - Returns data for user validation (NOT stored to database yet)
    """
    
    # Validate reply file type
    allowed_exts = ('.pdf', '.doc', '.docx')
    if not reply_file.filename.lower().endswith(allowed_exts):
        raise HTTPException(
            status_code=400, 
            detail="Reply document must be PDF or Word file (.pdf, .doc, .docx)"
        )
    
    try:
        # Initialize processor
        config = Config()
        pdf_processor = PDFProcessor(config)
        
        # Create temporary upload directory
        temp_dir = Path("./uploads/temp")
        temp_dir.mkdir(parents=True, exist_ok=True)
        
        # Save reply file temporarily to extract LAQ number
        temp_reply_path = temp_dir / reply_file.filename
        with temp_reply_path.open("wb") as buffer:
            shutil.copyfileobj(reply_file.file, buffer)
        
        # Extract LAQ data to get LAQ number
        laq_data = pdf_processor.process_pdf(str(temp_reply_path))
        laq_number = laq_data.laq_number
        
        if not laq_number or laq_number == "N/A":
            raise HTTPException(
                status_code=400,
                detail="Could not extract LAQ number from reply document"
            )
        
        # Create final storage directory
        storage_dir = Path(f"./uploads/{laq_number}")
        storage_dir.mkdir(parents=True, exist_ok=True)
        
        # Move reply file to final location
        final_reply_path = storage_dir / reply_file.filename
        shutil.move(str(temp_reply_path), str(final_reply_path))
        print(f"✅ Saved reply document: {final_reply_path}")
        
        # Save annexure files
        annexure_filenames = []
        for annexure in annexure_files:
            if annexure.filename:
                annexure_path = storage_dir / annexure.filename
                with annexure_path.open("wb") as buffer:
                    shutil.copyfileobj(annexure.file, buffer)
                annexure_filenames.append(annexure.filename)
                print(f"✅ Saved annexure: {annexure_path}")
        
        # Auto-link annexures to Q&A pairs
        qa_pairs_dict = [
            {
                "question": qa.question, 
                "answer": qa.answer, 
                "attachments": qa.attachments or [],
                "attachment_paths": []
            } 
            for qa in laq_data.qa_pairs
        ]
        
        if annexure_filenames:
            qa_pairs_dict = _auto_link_annexures(qa_pairs_dict, annexure_filenames)
        
        # Update LAQ data with linked annexures
        laq_data.qa_pairs = [
            type(laq_data.qa_pairs[0])(
                question=qa["question"],
                answer=qa["answer"],
                attachments=qa["attachments"]
            )
            for qa in qa_pairs_dict
        ]
        
        return ProcessingResponse(
            success=True,
            message=f"Processed {reply_file.filename}. Please validate the extracted data.",
            laq_data=laq_data,
            available_annexures=annexure_filenames,
            stored_directory=str(storage_dir)
        )
        
    except PDFProcessingError as e:
        raise HTTPException(status_code=400, detail=f"PDF processing failed: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Processing error: {str(e)}")


@router.post("/confirm", response_model=ConfirmStoreResponse)
async def confirm_and_store(request: ConfirmStoreRequest):
    """
    Confirm validated LAQ data and store to database.
    
    Step 2: User has validated/edited the data
    - Generates embeddings
    - Stores to ChromaDB with file paths
    - Completes the workflow
    """
    
    try:
        config = Config()
        embedding_service = EmbeddingService(config)
        db = LAQDatabase(config)
        
        laq_data = request.laq_data
        storage_dir = Path(request.stored_directory)
        
        # Find reply document in storage directory (should be PDF or Word file)
        reply_document_path = ""
        for file_path in storage_dir.glob("*"):
            if file_path.is_file() and file_path.suffix.lower() in ['.pdf', '.doc', '.docx']:
                # This is likely the reply document (not annexure)
                # Annexures typically have "annexure" in filename
                if "annexure" not in file_path.name.lower():
                    reply_document_path = str(file_path)
                    break
        
        # Build attachment_paths for each Q&A pair
        qa_pairs_dict = []
        for qa in laq_data.qa_pairs:
            attachment_paths = []
            if qa.attachments:
                for attachment in qa.attachments:
                    file_path = storage_dir / attachment
                    if file_path.exists():
                        attachment_paths.append(str(file_path))
            
            qa_pairs_dict.append({
                "question": qa.question,
                "answer": qa.answer,
                "attachments": qa.attachments or [],
                "attachment_paths": attachment_paths
            })
        
        # Prepare metadata
        laq_metadata = {
            'pdf_title': laq_data.pdf_title,
            'laq_type': laq_data.laq_type,
            'laq_number': laq_data.laq_number,
            'mla_name': laq_data.mla_name,
            'date': laq_data.date,
            'minister': laq_data.minister,
        }
        
        # Generate embeddings
        embeddings_list = embedding_service.embed_qa_pairs(
            qa_pairs=qa_pairs_dict,
            laq_metadata=laq_metadata if config.use_enhanced_context else None,
            use_enhanced_context=config.use_enhanced_context,
        )
        
        # Store to database
        laq_data_dict = {
            'pdf_title': laq_data.pdf_title,
            'laq_type': laq_data.laq_type,
            'laq_number': laq_data.laq_number,
            'mla_name': laq_data.mla_name,
            'date': laq_data.date,
            'minister': laq_data.minister,
            'attachments': [],
            'reply_document_path': reply_document_path,  # Add reply document path
            'qa_pairs': qa_pairs_dict
        }
        
        # Use LAQ number as pdf_name
        pdf_name = f"LAQ_{laq_data.laq_number}.pdf"
        
        stored_count = db.store_qa_pairs(
            laq_data=laq_data_dict,
            pdf_name=pdf_name,
            embeddings_list=embeddings_list,
        )
        
        return ConfirmStoreResponse(
            success=True,
            message=f"Successfully stored {stored_count} Q&A pairs to database",
            pdf_name=pdf_name,
            qa_pairs_stored=stored_count,
            laq_number=laq_data.laq_number
        )
        
    except EmbeddingError as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Embedding generation failed: {str(e)}"
        )
    except DatabaseError as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Database operation failed: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Storage error: {str(e)}")
