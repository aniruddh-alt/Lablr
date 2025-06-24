from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, String, DateTime, Enum, JSON
import enum

# Base class for declarative models
Base = declarative_base()

class DocumentStatus(enum.Enum):
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    PROCESSED = "processed"
    FAILED = "failed"
    LABELED = "labeled"
    DATASET_READY = "dataset_ready"

class Document(Base):
    __tablename__ = 'documents'

    id = Column(String, primary_key=True)
    filename = Column(String, nullable=False)
    description = Column(String)
    status = Column(Enum(DocumentStatus), nullable=False)
    upload_timestamp = Column(DateTime, nullable=False)
    processing_completed = Column(DateTime)
    job_id = Column(String)
    extracted_text = Column(String)
    labels = Column(JSON)
    confidence_scores = Column(JSON)

class JobStatus(enum.Enum):
    PENDING = "pending"
    STARTED = "started"
    SUCCESS = "success"
    FAILURE = "failure"
    RETRY = "retry"
    REVOKED = "revoked"

class Job(Base):
    __tablename__ = 'jobs'

    id = Column(String, primary_key=True)
    status = Column(Enum(JobStatus), nullable=False)
    result = Column(JSON)
    error = Column(String)
    created_at = Column(DateTime)
    completed_at = Column(DateTime)
    progress = Column(JSON)
