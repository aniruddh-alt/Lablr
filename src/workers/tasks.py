from celery import Celery
from celery.utils.log import get_task_logger
from typing import Dict, List, Any, Optional
import uuid
from datetime import datetime
import traceback
import os

from ..services.azure_form_recognizer import AzureFormRecognizerService
from ..services.azure_openai_service import AzureOpenAIService
from ..services.data_processor import DataProcessor
from ..core.config import get_settings
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
        
        # Combine results
        result = {
            'document_id': document_id,
            'status': 'completed',
            'extracted_text': extracted_data['content'],
            'text_extraction': extracted_data,
            'structure_analysis': structure_data,
            'processed_at': datetime.utcnow().isoformat()
        }
        
        logger.info(f"Successfully processed PDF document {document_id}")
        return result
        
    except Exception as e:
        logger.error(f"Error processing PDF {document_id}: {str(e)}")
        logger.error(traceback.format_exc())
        
        return {
            'document_id': document_id,
            'status': 'failed',
            'error': str(e),
            'processed_at': datetime.utcnow().isoformat()
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
        
        total_docs = len(document_data)
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
            self.update_state(
                state='PROGRESS',
                meta={
                    'current': i,
                    'total': total_docs,
                    'status': f'Processing documents {i+1}-{min(i+batch_size, total_docs)} of {total_docs}'
                }
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
        
        openai_service = get_openai_service()
        extraction_type = extraction_config['extraction_type']
        prompt = extraction_config['prompt']
        
        self.update_state(
            state='PROGRESS',
            meta={'status': f'Extracting data using {extraction_type}...'}
        )
        
        start_time = datetime.utcnow()
        
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
        
        processing_time = (datetime.utcnow() - start_time).total_seconds()
        
        return {
            'document_id': document_id,
            'status': 'success',
            'result': result,
            'processing_time': processing_time,
            'completed_at': datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error in single document extraction {document_id}: {str(e)}")
        return {
            'document_id': document_id,
            'status': 'failed',
            'error': str(e),
            'completed_at': datetime.utcnow().isoformat()
        }

@celery_app.task
def cleanup_temp_files():
    """Clean up temporary files and old outputs."""
    try:
        logger.info("Starting cleanup of temporary files")
        
        # Clean up old output files
        data_processor.cleanup_old_files(days_old=7)
        
        # Clean up old uploaded files (if needed)
        upload_dir = settings.upload_dir
        if os.path.exists(upload_dir):
            # Implementation for cleaning up old uploads
            pass
        
        logger.info("Completed cleanup of temporary files")
        
    except Exception as e:
        logger.error(f"Error during cleanup: {str(e)}")

# Periodic cleanup task (run daily)
from celery.schedules import crontab

celery_app.conf.beat_schedule = {
    'cleanup-temp-files': {
        'task': 'src.workers.tasks.cleanup_temp_files',
        'schedule': crontab(hour=2, minute=0),  # Run daily at 2 AM
    },
}
celery_app.conf.timezone = 'UTC' 