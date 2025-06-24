from fastapi import FastAPI, HTTPException, UploadFile, File, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime
import os

from ..core.config import get_settings
from ..models.document import DocumentCreate, DocumentResponse, DocumentStatus
from ..models.job import JobResponse, JobStatus
from ..models.extraction import (
    ExtractionJobCreate, ExtractionJobResponse, ExtractionResult,
    BatchExtractionStatus, OutputFormat, ExtractionType
)
from ..services.azure_form_recognizer import AzureFormRecognizerService
from ..services.azure_openai_service import AzureOpenAIService
from ..services.data_processor import DataProcessor
from ..workers.tasks import process_pdf_task, batch_extraction_task, single_document_extraction_task

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Lablr API",
    description="AI Data Labeler & ML Engineer API",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

settings = get_settings()

@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "message": "Lablr API is running",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/health")
async def health_check():
    """Detailed health check endpoint."""
    return {
        "status": "healthy",
        "services": {
            "api": "running",
            "database": "connected",  # Add actual DB check
            "azure_services": "configured"  # Add actual Azure service checks
        }
    }

@app.post("/documents/upload", response_model=DocumentResponse)
async def upload_document(
    file: UploadFile = File(...),
    description: Optional[str] = None
):
    """
    Upload a PDF document for processing.
    
    Args:
        file: PDF file to upload
        description: Optional description of the document
    
    Returns:
        Document metadata and processing job information
    """
    try:
        # Validate file type
        if not file.filename.lower().endswith('.pdf'):
            raise HTTPException(
                status_code=400,
                detail="Only PDF files are supported"
            )
        
        # Generate unique document ID
        document_id = str(uuid.uuid4())
        
        # Save file temporarily
        file_path = f"uploads/{document_id}_{file.filename}"
        
        # Read and save file content
        content = await file.read()
        with open(file_path, "wb") as f:
            f.write(content)
        
        # Create document record
        document = DocumentCreate(
            id=document_id,
            filename=file.filename,
            file_path=file_path,
            description=description,
            status=DocumentStatus.UPLOADED,
            upload_timestamp=datetime.utcnow()
        )
        
        # Start background processing
        job = process_pdf_task.delay(document_id, file_path)
        
        logger.info(f"Document {document_id} uploaded and processing started")
        
        return DocumentResponse(
            id=document.id,
            filename=document.filename,
            description=document.description,
            status=document.status,
            upload_timestamp=document.upload_timestamp,
            job_id=job.id
        )
        
    except Exception as e:
        logger.error(f"Error uploading document: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to upload document: {str(e)}"
        )

@app.get("/documents/{document_id}", response_model=DocumentResponse)
async def get_document(document_id: str):
    """
    Get document information by ID.
    
    Args:
        document_id: Unique document identifier
    
    Returns:
        Document metadata and current status
    """
    try:
        # TODO: Implement database query
        # For now, return mock data
        return DocumentResponse(
            id=document_id,
            filename="sample.pdf",
            status=DocumentStatus.PROCESSING,
            upload_timestamp=datetime.utcnow()
        )
        
    except Exception as e:
        logger.error(f"Error retrieving document {document_id}: {str(e)}")
        raise HTTPException(
            status_code=404,
            detail="Document not found"
        )

@app.get("/documents", response_model=List[DocumentResponse])
async def list_documents(
    skip: int = 0,
    limit: int = 100,
    status: Optional[DocumentStatus] = None
):
    """
    List all documents with optional filtering.
    
    Args:
        skip: Number of documents to skip
        limit: Maximum number of documents to return
        status: Optional status filter
    
    Returns:
        List of document metadata
    """
    try:
        # TODO: Implement database query with filters
        # For now, return empty list
        return []
        
    except Exception as e:
        logger.error(f"Error listing documents: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve documents"
        )

@app.get("/jobs/{job_id}", response_model=JobResponse)
async def get_job_status(job_id: str):
    """
    Get job status and results.
    
    Args:
        job_id: Celery job ID
    
    Returns:
        Job status and results
    """
    try:
        from ..workers.celery_app import celery_app
        
        # Get job result from Celery
        result = celery_app.AsyncResult(job_id)
        
        return JobResponse(
            id=job_id,
            status=JobStatus(result.status.lower()),
            result=result.result if result.ready() else None,
            error=str(result.info) if result.failed() else None
        )
        
    except Exception as e:
        logger.error(f"Error retrieving job {job_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve job status"
        )

@app.post("/documents/{document_id}/reprocess")
async def reprocess_document(document_id: str):
    """
    Reprocess a document with updated AI models.
    
    Args:
        document_id: Document to reprocess
    
    Returns:
        New job information
    """
    try:
        # TODO: Implement reprocessing logic
        return {"message": "Reprocessing started", "job_id": str(uuid.uuid4())}
        
    except Exception as e:
        logger.error(f"Error reprocessing document {document_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to start reprocessing"
        )

@app.get("/datasets")
async def list_datasets():
    """
    List available ML datasets generated from processed documents.
    
    Returns:
        List of available datasets
    """
    try:
        # TODO: Implement dataset listing
        return {"datasets": []}
        
    except Exception as e:
        logger.error(f"Error listing datasets: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve datasets"
        )

# ==================== EXTRACTION ENDPOINTS ====================

@app.post("/extraction/jobs", response_model=ExtractionJobResponse)
async def create_extraction_job(job: ExtractionJobCreate):
    """
    Create a new extraction job to process multiple documents with a custom prompt.
    
    Args:
        job: Extraction job configuration
    
    Returns:
        Extraction job information and status
    """
    try:
        # Generate unique job ID
        job_id = str(uuid.uuid4())
        
        # TODO: Validate that all document IDs exist and have been processed
        # For now, we'll assume they exist
        
        # Prepare document data for processing
        # In a real implementation, this would fetch the documents from a database
        document_data = []
        for doc_id in job.document_ids:
            # Mock document data - replace with actual database query
            document_data.append({
                'id': doc_id,
                'filename': f"document_{doc_id}.pdf",
                'text': f"Mock text content for document {doc_id}"  # Replace with actual extracted text
            })
        
        # Start background extraction job
        extraction_task = batch_extraction_task.delay(
            job_id=job_id,
            job_config=job.dict(),
            document_data=document_data
        )
        
        # Create response
        response = ExtractionJobResponse(
            id=job_id,
            name=job.name,
            description=job.description,
            document_ids=job.document_ids,
            extraction_type=job.extraction_type,
            output_format=job.output_format,
            prompt=job.prompt,
            status="started",
            created_at=datetime.utcnow(),
            progress={"task_id": extraction_task.id}
        )
        
        logger.info(f"Created extraction job {job_id} with {len(job.document_ids)} documents")
        return response
        
    except Exception as e:
        logger.error(f"Error creating extraction job: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create extraction job: {str(e)}"
        )

@app.get("/extraction/jobs/{job_id}", response_model=ExtractionJobResponse)
async def get_extraction_job(job_id: str):
    """
    Get extraction job status and results.
    
    Args:
        job_id: Unique job identifier
    
    Returns:
        Job status and results
    """
    try:
        from ..workers.celery_app import celery_app
        
        # TODO: Implement proper job tracking in database
        # For now, we'll return a mock response
        return ExtractionJobResponse(
            id=job_id,
            name="Sample Extraction Job",
            document_ids=["doc1", "doc2"],
            extraction_type=ExtractionType.STRUCTURED_DATA,
            output_format=OutputFormat.JSON,
            prompt="Extract key information",
            status="processing",
            created_at=datetime.utcnow()
        )
        
    except Exception as e:
        logger.error(f"Error retrieving extraction job {job_id}: {str(e)}")
        raise HTTPException(
            status_code=404,
            detail="Extraction job not found"
        )

@app.get("/extraction/jobs", response_model=List[ExtractionJobResponse])
async def list_extraction_jobs(
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = None
):
    """
    List extraction jobs with optional filtering.
    
    Args:
        skip: Number of jobs to skip
        limit: Maximum number of jobs to return
        status: Optional status filter
    
    Returns:
        List of extraction jobs
    """
    try:
        # TODO: Implement database query with filters
        return []
        
    except Exception as e:
        logger.error(f"Error listing extraction jobs: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve extraction jobs"
        )

@app.post("/extraction/single", response_model=Dict[str, Any])
async def extract_single_document(
    document_id: str,
    extraction_type: ExtractionType,
    prompt: str,
    output_format: OutputFormat = OutputFormat.JSON,
    custom_fields: Optional[Dict[str, str]] = None,
    num_questions: int = 10
):
    """
    Extract data from a single document immediately.
    
    Args:
        document_id: Document identifier
        extraction_type: Type of extraction to perform
        prompt: Extraction prompt
        output_format: Output format
        custom_fields: Optional custom field definitions
        num_questions: Number of questions for Q&A generation
    
    Returns:
        Extraction results
    """
    try:
        # TODO: Fetch document text from database
        # For now, use mock data
        document_text = f"Mock text content for document {document_id}"
        
        extraction_config = {
            'extraction_type': extraction_type,
            'prompt': prompt,
            'custom_fields': custom_fields,
            'num_questions': num_questions
        }
        
        # Start extraction task
        task = single_document_extraction_task.delay(
            document_id=document_id,
            document_text=document_text,
            extraction_config=extraction_config
        )
        
        return {
            'task_id': task.id,
            'document_id': document_id,
            'status': 'started',
            'message': 'Extraction started successfully'
        }
        
    except Exception as e:
        logger.error(f"Error starting single document extraction: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to start extraction: {str(e)}"
        )

@app.get("/extraction/jobs/{job_id}/download")
async def download_extraction_results(job_id: str):
    """
    Download extraction results file.
    
    Args:
        job_id: Job identifier
    
    Returns:
        File download response
    """
    try:
        # TODO: Implement file download from job results
        # This would typically stream the output file
        raise HTTPException(
            status_code=501,
            detail="File download not implemented yet"
        )
        
    except Exception as e:
        logger.error(f"Error downloading results for job {job_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to download results"
        )

@app.get("/extraction/jobs/{job_id}/status", response_model=BatchExtractionStatus)
async def get_extraction_job_status(job_id: str):
    """
    Get detailed status of extraction job.
    
    Args:
        job_id: Job identifier
    
    Returns:
        Detailed job status
    """
    try:
        # TODO: Implement detailed status tracking
        return BatchExtractionStatus(
            job_id=job_id,
            total_documents=10,
            processed_documents=5,
            successful_extractions=4,
            failed_extractions=1,
            current_document="processing document 6"
        )
        
    except Exception as e:
        logger.error(f"Error getting job status {job_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to get job status"
        )

# ==================== BULK UPLOAD ENDPOINTS ====================

@app.post("/documents/upload/bulk")
async def upload_documents_bulk(
    files: List[UploadFile] = File(...),
    description: Optional[str] = None
):
    """
    Upload multiple PDF documents at once.
    
    Args:
        files: List of PDF files to upload
        description: Optional description for the batch
    
    Returns:
        Upload results for each file
    """
    try:
        results = []
        
        for file in files:
            # Validate file type
            if not file.filename.lower().endswith('.pdf'):
                results.append({
                    'filename': file.filename,
                    'status': 'error',
                    'error': 'Only PDF files are supported'
                })
                continue
            
            try:
                # Generate unique document ID
                document_id = str(uuid.uuid4())
                
                # Save file temporarily
                file_path = f"uploads/{document_id}_{file.filename}"
                
                # Create uploads directory if it doesn't exist
                os.makedirs("uploads", exist_ok=True)
                
                # Read and save file content
                content = await file.read()
                with open(file_path, "wb") as f:
                    f.write(content)
                
                # Start background processing
                job = process_pdf_task.delay(document_id, file_path)
                
                results.append({
                    'filename': file.filename,
                    'document_id': document_id,
                    'status': 'uploaded',
                    'job_id': job.id
                })
                
            except Exception as file_error:
                results.append({
                    'filename': file.filename,
                    'status': 'error',
                    'error': str(file_error)
                })
        
        logger.info(f"Bulk upload completed: {len(files)} files processed")
        return {
            'message': f'Processed {len(files)} files',
            'results': results,
            'successful_uploads': len([r for r in results if r['status'] == 'uploaded']),
            'failed_uploads': len([r for r in results if r['status'] == 'error'])
        }
        
    except Exception as e:
        logger.error(f"Error in bulk upload: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process bulk upload: {str(e)}"
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
