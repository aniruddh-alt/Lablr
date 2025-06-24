from pydantic import BaseModel, Field
from enum import Enum
from datetime import datetime
from typing import Optional, List, Dict, Any, Union

class OutputFormat(str, Enum):
    """Output format for extracted data."""
    CSV = "csv"
    JSON = "json"
    JSONL = "jsonl"
    QA_PAIRS = "qa_pairs"
    MARKDOWN = "markdown"
    XLSX = "xlsx"

class ExtractionType(str, Enum):
    """Type of extraction to perform."""
    STRUCTURED_DATA = "structured_data"
    QA_GENERATION = "qa_generation"
    SUMMARIZATION = "summarization"
    CLASSIFICATION = "classification"
    ENTITY_EXTRACTION = "entity_extraction"
    CUSTOM_PROMPT = "custom_prompt"

class ExtractionJobCreate(BaseModel):
    """Schema for creating a new extraction job."""
    name: str = Field(..., description="Name of the extraction job")
    description: Optional[str] = Field(None, description="Description of what to extract")
    document_ids: List[str] = Field(..., description="List of document IDs to process")
    extraction_type: ExtractionType = Field(..., description="Type of extraction to perform")
    output_format: OutputFormat = Field(default=OutputFormat.JSON, description="Output format")
    prompt: str = Field(..., description="Extraction prompt describing what to extract")
    
    # Advanced options
    batch_size: int = Field(default=5, ge=1, le=50, description="Number of documents to process in parallel")
    include_confidence: bool = Field(default=True, description="Include confidence scores in output")
    include_source_refs: bool = Field(default=True, description="Include source references")
    custom_fields: Optional[Dict[str, str]] = Field(None, description="Custom field definitions")
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "Invoice Data Extraction",
                "description": "Extract key information from invoices",
                "document_ids": ["doc1", "doc2", "doc3"],
                "extraction_type": "structured_data",
                "output_format": "csv",
                "prompt": "Extract the following fields from each invoice: company_name, invoice_number, date, total_amount, tax_amount, line_items with descriptions and amounts",
                "batch_size": 10,
                "include_confidence": True,
                "custom_fields": {
                    "company_name": "The name of the company issuing the invoice",
                    "invoice_number": "The unique invoice identifier",
                    "total_amount": "The total amount due including tax"
                }
            }
        }

class ExtractionJobResponse(BaseModel):
    """Schema for extraction job response."""
    id: str
    name: str
    description: Optional[str]
    document_ids: List[str]
    extraction_type: ExtractionType
    output_format: OutputFormat
    prompt: str
    status: str
    created_at: datetime
    completed_at: Optional[datetime] = None
    progress: Dict[str, Any] = Field(default_factory=dict)
    results: Optional[Dict[str, Any]] = None
    output_file_path: Optional[str] = None
    error_message: Optional[str] = None
    
    class Config:
        from_attributes = True

class ExtractionResult(BaseModel):
    """Schema for individual document extraction result."""
    document_id: str
    filename: str
    status: str
    extracted_data: Dict[str, Any]
    confidence_scores: Optional[Dict[str, float]] = None
    source_references: Optional[List[Dict[str, Any]]] = None
    processing_time: Optional[float] = None
    error_message: Optional[str] = None

class BatchExtractionStatus(BaseModel):
    """Schema for batch extraction status."""
    job_id: str
    total_documents: int = 0
    processed_documents: int = 0
    successful_extractions: int = 0
    failed_extractions: int = 0
    estimated_completion: Optional[datetime] = None
    current_document: Optional[str] = None 