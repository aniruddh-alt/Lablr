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
        update_document_status(document_id, "PROCESSING", job_id=self.request.id)
        
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
            "success", 
            result=result,
            completed_at=processing_completed
        )
        
        # Update document status
        update_document_status(
            document_id, 
            "processed",
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
        update_document_status(document_id, "failed")
        
        # Update job status to failed
        if hasattr(self, 'request') and hasattr(self.request, 'id'):
            update_job_status(
                self.request.id, 
                "failure", 
                error=str(e),
                completed_at=datetime.now()
            )
        
        return {
            'document_id': document_id,
            'status': 'failed',
            'error': str(e),
            'processed_at': datetime.now().isoformat()
        }

@celery_app.task(bind=True)
def batch_extraction_task(
    self,
    job_id: str,
    job_config: Dict[str, Any],
    document_data: List[Dict[str, Any]]
):
    """
    Process batch extraction job with multiple documents.
    
    Args:
        job_id: Unique job identifier
        job_config: Job configuration including prompt and settings
        document_data: List of documents with their extracted text
        
    Returns:
        Batch processing results
    """
    try:
        logger.info(f"Starting batch extraction job {job_id}")
        
        # Update job status to started
        update_job_status(
            job_id,
            "started", 
            progress={"status": "starting", "progress": 0}
        )
        
        # If document_data is empty, we need to fetch documents from the database
        if not document_data:
            document_ids = job_config.get('document_ids', [])
            if document_ids:
                try:
                    db = SessionLocal()
                    db_docs = db.query(DBDocument).filter(DBDocument.id.in_(document_ids)).all()
                    
                    document_data = []
                    for doc in db_docs:
                        if doc.extracted_text:  # Only include documents with extracted text
                            document_data.append({
                                'id': doc.id,
                                'filename': doc.filename,
                                'text': doc.extracted_text
                            })
                    
                    db.close()
                except Exception as db_error:
                    logger.error(f"Error fetching documents from database: {str(db_error)}")
                    update_job_status(
                    job_id, 
                    "failure", 
                    error=f"Failed to fetch documents: {str(db_error)}",
                    completed_at=datetime.now()
                )
                    return {
                        'status': 'failed',
                        'error': f"Failed to fetch documents: {str(db_error)}",
                        'job_id': job_id
                    }
        
        total_docs = len(document_data)
        if total_docs == 0:
            update_job_status(
                job_id, 
                "failure", 
                error="No documents to process",
                completed_at=datetime.now()
            )
            return {
                'status': 'failed',
                'error': "No documents to process",
                'job_id': job_id
            }
        
        results = []
        
        # Initialize OpenAI service
        openai_service = get_openai_service()
        
        # Process documents in batches
        batch_size = job_config.get('batch_size', 5)
        extraction_type = job_config['extraction_type']
        prompt = job_config['prompt']
        
        for i in range(0, total_docs, batch_size):
            batch = document_data[i:i + batch_size]
            
            # Update progress
            progress_pct = int((i / total_docs) * 100) if total_docs > 0 else 0
            progress_info = {
                'current': i,
                'total': total_docs,
                'percent': progress_pct,
                'status': f'Processing documents {i+1}-{min(i+batch_size, total_docs)} of {total_docs}'
            }
            
            self.update_state(
                state='PROGRESS',
                meta=progress_info
            )
            
            # Update job status in database
            update_job_status(
                job_id,
                "started",
                progress=progress_info
            )
            
            # Process batch based on extraction type
            for doc in batch:
                try:
                    start_time = datetime.utcnow()
                    
                    if extraction_type == "structured_data":
                        result = openai_service.extract_structured_data(
                            document_text=doc['text'],
                            extraction_prompt=prompt,
                            custom_fields=job_config.get('custom_fields')
                        )
                    elif extraction_type == "qa_generation":
                        result = openai_service.generate_qa_pairs(
                            document_text=doc['text'],
                            qa_prompt=prompt,
                            num_questions=job_config.get('num_questions', 10)
                        )
                    elif extraction_type == "summarization":
                        result = openai_service.summarize_document(
                            document_text=doc['text'],
                            summary_prompt=prompt
                        )
                    elif extraction_type == "entity_extraction":
                        result = openai_service.extract_entities(
                            document_text=doc['text'],
                            entity_prompt=prompt
                        )
                    elif extraction_type == "classification":
                        result = openai_service.classify_document(
                            document_text=doc['text'],
                            classification_prompt=prompt
                        )
                    else:
                        result = openai_service.extract_structured_data(
                            document_text=doc['text'],
                            extraction_prompt=prompt
                        )
                    
                    processing_time = (datetime.utcnow() - start_time).total_seconds()
                    
                    results.append({
                        'document_id': doc['id'],
                        'filename': doc['filename'],
                        'status': 'success',
                        'result': result,
                        'processing_time': processing_time
                    })
                    
                except Exception as doc_error:
                    logger.error(f"Error processing document {doc['id']}: {str(doc_error)}")
                    results.append({
                        'document_id': doc['id'],
                        'filename': doc['filename'],
                        'status': 'error',
                        'error': str(doc_error)
                    })
        
        # Process results into output format
        self.update_state(
            state='PROGRESS',
            meta={
                'current': total_docs,
                'total': total_docs,
                'status': 'Formatting output...'
            }
        )
        
        output_info = data_processor.process_extraction_results(
            results=results,
            output_format=job_config['output_format'],
            extraction_type=extraction_type,
            job_name=job_config['name']
        )
        
        # Final results
        final_result = {
            'job_id': job_id,
            'status': 'completed',
            'total_documents': total_docs,
            'successful_extractions': len([r for r in results if r['status'] == 'success']),
            'failed_extractions': len([r for r in results if r['status'] == 'error']),
            'output_file': output_info,
            'results': results,
            'completed_at': datetime.utcnow().isoformat()
        }
        
        logger.info(f"Successfully completed batch extraction job {job_id}")
        return final_result
        
    except Exception as e:
        logger.error(f"Error in batch extraction job {job_id}: {str(e)}")
        logger.error(traceback.format_exc())
        
        return {
            'job_id': job_id,
            'status': 'failed',
            'error': str(e),
            'completed_at': datetime.utcnow().isoformat()
        }

@celery_app.task(bind=True)
def single_document_extraction_task(
    self,
    document_id: str,
    document_text: str,
    extraction_config: Dict[str, Any]
):
    """
    Extract data from a single document.
    
    Args:
        document_id: Document identifier
        document_text: Text content of the document
        extraction_config: Extraction configuration
        
    Returns:
        Extraction results
    """
    try:
        logger.info(f"Starting single document extraction for {document_id}")
        
        # Update document status to processing
        update_document_status(document_id, "PROCESSING", job_id=self.request.id)
        
        openai_service = get_openai_service()
        extraction_type = extraction_config['extraction_type']
        prompt = extraction_config['prompt']
        
        self.update_state(
            state='PROGRESS',
            meta={'status': f'Extracting data using {extraction_type}...'}
        )
        
        start_time = datetime.now()
        
        if extraction_type == "structured_data":
            result = openai_service.extract_structured_data(
                document_text=document_text,
                extraction_prompt=prompt,
                custom_fields=extraction_config.get('custom_fields')
            )
        elif extraction_type == "qa_generation":
            result = openai_service.generate_qa_pairs(
                document_text=document_text,
                qa_prompt=prompt,
                num_questions=extraction_config.get('num_questions', 10)
            )
        elif extraction_type == "summarization":
            result = openai_service.summarize_document(
                document_text=document_text,
                summary_prompt=prompt
            )
        elif extraction_type == "entity_extraction":
            result = openai_service.extract_entities(
                document_text=document_text,
                entity_prompt=prompt
            )
        elif extraction_type == "classification":
            result = openai_service.classify_document(
                document_text=document_text,
                classification_prompt=prompt
            )
        else:
            result = openai_service.extract_structured_data(
                document_text=document_text,
                extraction_prompt=prompt
            )
        
        processing_time = (datetime.now() - start_time).total_seconds()
        completion_time = datetime.now()
        
        # Extract the confidence scores if available
        confidence_scores = {}
        if isinstance(result, dict) and "confidence" in result:
            confidence_scores["overall"] = result["confidence"]
        
        # Extract labels from result based on extraction type
        labels = None
        if extraction_type == "structured_data" and "extracted_data" in result:
            labels = result["extracted_data"]
        elif extraction_type == "qa_generation" and "qa_pairs" in result:
            labels = {"qa_pairs": result["qa_pairs"]}
        elif extraction_type == "entity_extraction":
            labels = {k: v for k, v in result.items() if isinstance(result, dict) and k not in ["model_used", "entity_prompt", "processed_at", "token_usage"]}
        elif extraction_type == "classification" and "primary_class" in result:
            labels = {
                "primary_class": result["primary_class"],
                "sub_classes": result.get("sub_classes", []),
                "confidence": result.get("confidence", 0)
            }
        
        # Update document status to labeled with labels and confidence scores
        update_document_status(
            document_id, 
            "LABELED", 
            labels=labels, 
            confidence_scores=confidence_scores,
            processing_completed=completion_time
        )
        
        # Update job status if we have a job ID
        if hasattr(self, 'request') and hasattr(self.request, 'id'):
            update_job_status(
                self.request.id, 
                "success", 
                result=result,
                completed_at=completion_time
            )
        
        return {
            'document_id': document_id,
            'status': 'success',
            'result': result,
            'processing_time': processing_time,
            'completed_at': completion_time.isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error in single document extraction {document_id}: {str(e)}")
        
        # Update document status to failed
        update_document_status(document_id, "failed")
        
        # Update job status if we have a job ID
        if hasattr(self, 'request') and hasattr(self.request, 'id'):
            update_job_status(
                self.request.id, 
                "failure", 
                error=str(e),
                completed_at=datetime.now()
            )
        
        return {
            'document_id': document_id,
            'status': 'failed',
            'error': str(e),
            'completed_at': datetime.now().isoformat()
        }

def update_document_status(document_id: str, status: str, **kwargs):
    """
    Update document status in the database.
    
    Args:
        document_id: Document ID
        status: New status
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
            document.status = ORMDocumentStatus(status)
            
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

def update_job_status(job_id: str, status: str, **kwargs):
    """
    Update job status in the database.
    
    Args:
        job_id: Job ID
        status: New status
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
            job.status = ORMJobStatus(status)
            
            # Update additional fields
            if "result" in kwargs:
                job.result = kwargs["result"]
                
            if "error" in kwargs:
                job.error = kwargs["error"]
                
            if "completed_at" in kwargs:
                job.completed_at = kwargs["completed_at"]
            elif status in ["success", "failure", "revoked"]:
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

@celery_app.task(bind=True)
def cleanup_temp_files(self, days_old: int = 7):
    """
    Clean up temporary files older than specified days.
    
    Args:
        days_old: Days threshold for cleanup
    """
    try:
        logger.info(f"Starting cleanup of files older than {days_old} days")
        
        # Define directories to clean
        upload_dir = settings.upload_dir
        output_dir = settings.output_dir
        
        # Calculate cutoff time
        now = datetime.now()
        cutoff = now.timestamp() - (days_old * 24 * 60 * 60)
        
        # Clean upload directory
        upload_count = 0
        if os.path.exists(upload_dir):
            for filename in os.listdir(upload_dir):
                filepath = os.path.join(upload_dir, filename)
                if os.path.isfile(filepath):
                    mtime = os.path.getmtime(filepath)
                    if mtime < cutoff:
                        os.remove(filepath)
                        upload_count += 1
        
        # Clean output directory
        output_count = 0
        if os.path.exists(output_dir):
            for filename in os.listdir(output_dir):
                filepath = os.path.join(output_dir, filename)
                if os.path.isfile(filepath):
                    mtime = os.path.getmtime(filepath)
                    if mtime < cutoff:
                        os.remove(filepath)
                        output_count += 1
        
        logger.info(f"Cleanup completed: removed {upload_count} upload files and {output_count} output files")
        return {
            "status": "completed",
            "upload_files_removed": upload_count,
            "output_files_removed": output_count
        }
        
    except Exception as e:
        logger.error(f"Error during file cleanup: {str(e)}")
        return {
            "status": "failed",
            "error": str(e)
        }

# Periodic cleanup task (run daily)
from celery.schedules import crontab

celery_app.conf.beat_schedule = {
    'cleanup-temp-files': {
        'task': 'src.workers.tasks.cleanup_temp_files',
        'schedule': crontab(hour=2, minute=0),  # Run daily at 2 AM
    },
}
celery_app.conf.timezone = 'UTC'