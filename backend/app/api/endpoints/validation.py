"""Validation API endpoints for checking annexure and LAQ references."""

from fastapi import APIRouter, HTTPException, Query

from app.models.schemas import AnnexureUsageStats, ValidationReport, ValidationSummary
from app.services.config import Config
from app.services.validation import ValidationError, ValidationService

router = APIRouter()


@router.get("/laq/{laq_number}", response_model=ValidationReport)
async def validate_laq_references(
    laq_number: str, pdf_name: str = Query(..., description="PDF name to validate")
):
    """Validate annexure references for a specific LAQ.

    Returns validation report showing missing and unreferenced annexures.
    """
    try:
        config = Config()
        validator = ValidationService(config)
        report = validator.validate_laq_annexure_references(laq_number, pdf_name)
        return ValidationReport(**report)
    except ValidationError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {e}")


@router.get("/all", response_model=ValidationSummary)
async def validate_all_laqs():
    """Validate annexure references for all LAQs in the database.

    Returns summary report for all LAQs.
    """
    try:
        config = Config()
        validator = ValidationService(config)
        report = validator.validate_all_laqs()
        return ValidationSummary(**report)
    except ValidationError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {e}")


@router.get("/stats", response_model=AnnexureUsageStats)
async def get_annexure_usage_stats():
    """Get statistics about annexure usage across all LAQs.

    Returns usage statistics and reference analysis.
    """
    try:
        config = Config()
        validator = ValidationService(config)
        stats = validator.get_annexure_usage_stats()
        return AnnexureUsageStats(**stats)
    except ValidationError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {e}")
