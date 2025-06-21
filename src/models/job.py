from pydantic import BaseModel
from enum import Enum
from datetime import datetime
from typing import Optional, Any

class JobStatus(str, Enum):
    """Job processing status."""
    PENDING = "pending"
    STARTED = "started"
    SUCCESS = "success"
    FAILURE = "failure"
    RETRY = "retry"
    REVOKED = "revoked"

class JobResponse(BaseModel):
    """Schema for job response."""
    id: str
    status: JobStatus
    result: Optional[Any] = None
    error: Optional[str] = None
    created_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    progress: Optional[dict] = None
    
    class Config:
        from_attributes = True

class JobCreate(BaseModel):
    """Schema for creating a new job."""
    job_type: str
    document_id: str
    parameters: Optional[dict] = None
