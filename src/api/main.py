from fastapi import FastAPI, HTTPException, UploadFile, File, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging
from typing import List, Optional
import uuid
from datetime import datetime

from ..core.config import get_settings
from ..models.document import DocumentCreate, DocumentResponse, DocumentStatus
from ..models.job import JobResponse, JobStatus
from ..services.pdf_processor import PDFProcessorService
from ..services.azure_form_recognizer import AzureFormRecognizerService
from ..services.azure_cognitive import AzureCognitiveService
from ..workers.tasks import process_pdf_task

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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
