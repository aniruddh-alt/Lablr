from celery import Celery
from celery.utils.log import get_task_logger
from typing import Dict, List, Any, Optional
import uuid
from datetime import datetime
import traceback
import os

from sqlalchemy.orm import Session

from ..models.models import Document as DBDocument, DocumentStatus as ORMDocumentStatus, Job as DBJob, JobStatus as ORMJobStatus
from ..services.azure_form_recognizer import AzureFormRecognizerService
from ..services.azure_openai_service import AzureOpenAIService
from ..services.data_processor import DataProcessor
from ..core.config import get_settings
from ..core.database import SessionLocal
from ..workers.celery_app import celery_app

logger = get_task_logger(__name__)
settings = get_settings()

# Initialize services
form_recognizer = None
openai_service = None
data_processor = DataProcessor()

def get_form_recognizer():
    """Get or create Form Recognizer service instance."""
    global form_recognizer
    if form_recognizer is None:
        if settings.azure_form_recognizer_endpoint and settings.azure_form_recognizer_key:
            form_recognizer = AzureFormRecognizerService(
                endpoint=settings.azure_form_recognizer_endpoint,
                credential=settings.azure_form_recognizer_key
            )
        else:
            logger.error("Azure Form Recognizer credentials not configured")
            raise ValueError("Azure Form Recognizer credentials not configured")
    return form_recognizer

def get_openai_service():
    """Get or create OpenAI service instance."""
    global openai_service
    if openai_service is None:
        # Try new configuration first, then fall back to legacy
        endpoint = settings.azure_openai_endpoint or settings.azure_cognitive_services_endpoint
        api_key = settings.azure_openai_key or settings.azure_cognitive_services_key
        
        if endpoint and api_key:
            openai_service = AzureOpenAIService(
                endpoint=endpoint,
                api_key=api_key,
                api_version=settings.azure_openai_api_version
            )
        else:
            logger.error("Azure OpenAI credentials not configured")
            raise ValueError("Azure OpenAI credentials not configured")
    return openai_service

@celery_app.task(bind=True)
def process_pdf_task(self, document_id: str, file_path: str):
    """
    Process a single PDF document using Azure Form Recognizer.
    
    Args:
        document_id: Unique document identifier
        file_path: Path to the PDF file
        
    Returns:
        Processing results
    """
    try:
        logger.info(f"Starting PDF processing for document {document_id}")
        
        # Update document status in database
        update_document_status(document_id, ORMDocumentStatus.PROCESSING, job_id=self.request.id)
        
        # Update task status
        self.update_state(
            state='PROGRESS',
            meta={
                'current': 1,
                'total': 3,
                'status': 'Extracting text from PDF...'
            }
        )
        
        # Extract text using Form Recognizer
        form_recognizer_service = get_form_recognizer()
        extracted_data = form_recognizer_service.extract_text_from_pdf(file_path)
        
        self.update_state(
            state='PROGRESS',
            meta={
                'current': 2,
                'total': 3,
                'status': 'Analyzing document structure...'
            }
        )
        
        # Analyze document structure
        structure_data = form_recognizer_service.analyze_document_structure(file_path)
        
        self.update_state(
            state='PROGRESS',
            meta={
                'current': 3,
                'total': 3,
                'status': 'Finalizing results...'
            }
        )
        
        # Extract key-value pairs if available
        kv_data = None
        try:
            kv_data = form_recognizer_service.extract_key_value_pairs(file_path)
        except Exception as kv_error:
            logger.warning(f"Key-value extraction failed: {str(kv_error)}")
        
        # Process completion time
        processing_completed = datetime.now()
        
        # Combine results
        result = {
            'document_id': document_id,
            'status': 'completed',
            'extracted_text': extracted_data['content'],
            'text_extraction': extracted_data,
            'structure_analysis': structure_data,
            'key_values': kv_data,
            'processed_at': processing_completed.isoformat()
        }
        
        # Update job status
        update_job_status(
            self.request.id, 
            ORMJobStatus.SUCCESS, 
            result=result,
            completed_at=processing_completed
        )
        
        # Update document status
        update_document_status(
            document_id, 
            ORMDocumentStatus.PROCESSED,
            extracted_text=extracted_data['content'],
            processing_completed=processing_completed,
            confidence_scores={'text_extraction': extracted_data.get('confidence', 0.0)}
        )
        
        logger.info(f"Successfully processed PDF document {document_id}")
        return result
        
    except Exception as e:
        logger.error(f"Error processing PDF {document_id}: {str(e)}")
        logger.error(traceback.format_exc())
        
        # Update document status to failed
        update_document_status(document_id, ORMDocumentStatus.FAILED)
        
        # Update job status to failed
        if hasattr(self, 'request') and hasattr(self.request, 'id'):
            update_job_status(
                self.request.id, 
                ORMJobStatus.FAILURE, 
                error=str(e),
                completed_at=datetime.now()
            )
        
        return {
            'document_id': document_id,
            'status': 'failed',
            'error': str(e),
            'processed_at': datetime.now().isoformat()
        }

# ... [rest of the functions] ...

def update_document_status(document_id: str, status: ORMDocumentStatus, **kwargs):
    """
    Update document status in the database.
    
    Args:
        document_id: Document ID
        status: New status (using the enum directly, not a string)
        **kwargs: Additional fields to update
    """
    try:
        db = SessionLocal()
        try:
            # Find document in the database
            document = db.query(DBDocument).filter(DBDocument.id == document_id).first()
            if not document:
                logger.warning(f"Document {document_id} not found in database")
                return False
            
            # Update status
            document.status = status
            
            # Update additional fields
            if "extracted_text" in kwargs:
                document.extracted_text = kwargs["extracted_text"]
                
            if "processing_completed" in kwargs:
                document.processing_completed = kwargs["processing_completed"]
            else:
                document.processing_completed = datetime.now()
                
            if "labels" in kwargs:
                document.labels = kwargs["labels"]
                
            if "confidence_scores" in kwargs:
                document.confidence_scores = kwargs["confidence_scores"]
                
            if "job_id" in kwargs:
                document.job_id = kwargs["job_id"]
            
            db.commit()
            logger.info(f"Updated document {document_id} status to {status}")
            return True
            
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Error updating document status: {str(e)}")
        logger.error(traceback.format_exc())
        return False

def update_job_status(job_id: str, status: ORMJobStatus, **kwargs):
    """
    Update job status in the database.
    
    Args:
        job_id: Job ID
        status: New status (using the enum directly, not a string)
        **kwargs: Additional fields to update
    """
    try:
        db = SessionLocal()
        try:
            # Find job in the database
            job = db.query(DBJob).filter(DBJob.id == job_id).first()
            if not job:
                logger.warning(f"Job {job_id} not found in database")
                return False
            
            # Update status
            job.status = status
            
            # Update additional fields
            if "result" in kwargs:
                job.result = kwargs["result"]
                
            if "error" in kwargs:
                job.error = kwargs["error"]
                
            if "completed_at" in kwargs:
                job.completed_at = kwargs["completed_at"]
            elif status in [ORMJobStatus.SUCCESS, ORMJobStatus.FAILURE, ORMJobStatus.REVOKED]:
                job.completed_at = datetime.now()
                
            if "progress" in kwargs:
                job.progress = kwargs["progress"]
            
            db.commit()
            logger.info(f"Updated job {job_id} status to {status}")
            return True
            
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Error updating job status: {str(e)}")
        logger.error(traceback.format_exc())
        return False
