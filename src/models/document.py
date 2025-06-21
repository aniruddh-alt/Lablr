from pydantic import BaseModel
from enum import Enum
from datetime import datetime
from typing import Optional

class DocumentStatus(str, Enum):
    """Document processing status."""
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    PROCESSED = "processed"
    FAILED = "failed"
    LABELED = "labeled"
    DATASET_READY = "dataset_ready"

class DocumentCreate(BaseModel):
    """Schema for creating a new document."""
    id: str
    filename: str
    file_path: str
    description: Optional[str] = None
    status: DocumentStatus = DocumentStatus.UPLOADED
    upload_timestamp: datetime

class DocumentResponse(BaseModel):
    """Schema for document response."""
    id: str
    filename: str
    description: Optional[str] = None
    status: DocumentStatus
    upload_timestamp: datetime
    processing_completed: Optional[datetime] = None
    job_id: Optional[str] = None
    extracted_text: Optional[str] = None
    labels: Optional[dict] = None
    confidence_scores: Optional[dict] = None
    
    class Config:
        from_attributes = True

class DocumentUpdate(BaseModel):
    """Schema for updating document."""
    description: Optional[str] = None
    status: Optional[DocumentStatus] = None
    extracted_text: Optional[str] = None
    labels: Optional[dict] = None
    confidence_scores: Optional[dict] = None
