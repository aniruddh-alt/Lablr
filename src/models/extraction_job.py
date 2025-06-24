from sqlalchemy import Column, String, JSON, DateTime, func
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
from ..models.models import Base

class ExtractionJob(Base):
    __tablename__ = 'extraction_jobs'
    
    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(String)
    document_ids = Column(JSON, nullable=False)
    extraction_type = Column(String, nullable=False)
    output_format = Column(String, nullable=False)
    prompt = Column(String)
    status = Column(String, nullable=False, default="started")
    created_at = Column(DateTime, nullable=False, default=func.now())
    completed_at = Column(DateTime)
    result = Column(JSON)
    output_file_path = Column(String)
    error_message = Column(String)
    progress = Column(JSON)
