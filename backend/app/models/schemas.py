"""
Pydantic models for API request/response schemas.
"""

from typing import Dict, List, Optional

from pydantic import BaseModel, Field


# Request/Response Models
class QAPairResponse(BaseModel):
    """Model for a question-answer pair."""

    question: str = Field(min_length=0, description="The question text")
    answer: str = Field(min_length=0, description="The answer text")
    attachments: Optional[List[str]] = Field(default=None, description="List of attachments")


class LAQDataResponse(BaseModel):
    """Model for structured LAQ data."""

    pdf_title: str = Field(default="", description="Title of the LAQ document")
    laq_type: str = Field(default="", description="Type of LAQ (e.g., Starred, Unstarred)")
    laq_number: str = Field(description="LAQ identification number")
    minister: str = Field(description="Name of the minister")
    date: str = Field(description="Date of the LAQ")
    mla_name: Optional[str] = Field(default=None, description="Person who tabled the question")
    qa_pairs: List[QAPairResponse] = Field(min_items=1, description="List of question-answer pairs")
    # attachments: List[str] = Field(default_factory=list, description="List of document-level attachments")
    



class SearchQuery(BaseModel):
    """Search query request model."""

    query: str = Field(..., min_length=1, description="Search query text")
    top_k: Optional[int] = Field(
        5, ge=1, le=20, description="Number of results to return"
    )
    threshold: Optional[float] = Field(
        0.6, ge=0.0, le=1.0, description="Similarity threshold"
    )


class SearchResult(BaseModel):
    """Single search result."""

    question: str
    answer: str
    metadata: dict
    similarity_score: float
    reply_document_url: Optional[str] = Field(default=None, description="URL to download reply document")
    attachment_urls: List[str] = Field(default_factory=list, description="URLs to download annexure files")


class SearchResponse(BaseModel):
    """Search results response."""

    query: str
    results: List[SearchResult]
    total_results: int


class ChatQuery(BaseModel):
    """Chat query request model."""

    question: str = Field(..., min_length=1, description="User question")
    top_k: Optional[int] = Field(5, ge=1, le=20, description="Number of context LAQs")


class ChatResponse(BaseModel):
    """Chat response model."""

    question: str
    answer: str
    sources: List[SearchResult]


class UploadResponse(BaseModel):
    """PDF upload response model."""

    success: bool
    message: str
    pdf_name: str
    qa_pairs_extracted: int
    laq_data: Optional[LAQDataResponse] = None


class AnnexureUploadResponse(BaseModel):
    """Annexure upload response model."""

    success: bool
    message: str
    laq_number: str
    annexure_label: str
    stored_id: str


class DatabaseInfo(BaseModel):
    """Database information response."""

    collection_name: str
    total_documents: int
    database_path: str
    similarity_metric: str
    embedding_model: str
    llm_model: str


class HealthCheck(BaseModel):
    """Health check response."""

    status: str
    ollama_running: bool
    database: str


class ValidationReport(BaseModel):
    """Validation report for a single LAQ."""

    laq_number: str
    pdf_name: str
    total_laq_documents: int
    total_annexures: int
    referenced_annexures: List[str]
    available_annexures: List[str]
    missing_annexures: List[str]
    unreferenced_annexures: List[str]
    validation_status: str
    issues: List[str]


class ValidationSummary(BaseModel):
    """Summary validation report for all LAQs."""

    total_laqs_validated: int
    total_with_issues: int
    validation_reports: List[ValidationReport]
    summary: Dict


class AnnexureUsageStats(BaseModel):
    """Annexure usage statistics."""

    total_annexure_documents: int
    unique_annexure_labels: int
    total_references_in_laqs: int
    unique_referenced_annexures: int
    annexure_usage_breakdown: Dict
    unreferenced_annexures: List[str]
    referenced_but_missing: List[str]


class ProcessingResponse(BaseModel):
    """Response after processing LAQ for validation (not stored yet)."""
    
    success: bool
    message: str
    laq_data: LAQDataResponse
    available_annexures: List[str] = Field(default_factory=list, description="List of uploaded annexure filenames")
    stored_directory: str = Field(description="Directory where files are stored")


class ConfirmStoreRequest(BaseModel):
    """Request to confirm and store validated LAQ data."""
    
    laq_data: LAQDataResponse
    stored_directory: str = Field(description="Directory where files are stored")


class ConfirmStoreResponse(BaseModel):
    """Response after confirming and storing LAQ to database."""
    
    success: bool
    message: str
    pdf_name: str
    qa_pairs_stored: int
    laq_number: str
