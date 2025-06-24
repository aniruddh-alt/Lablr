#!/usr/bin/env python3
"""
Lablr Document Upload Test Script

This script uploads a PDF document to the Lablr API and monitors the processing status.
"""

import requests
import json
import time
import sys
import os

# Configuration
API_BASE_URL = "http://localhost:8002"
PDF_PATH = "test_files/sample_invoice.pdf"
POLL_INTERVAL = 2  # seconds

def upload_document(file_path, description=None):
    """Upload document to the API."""
    print("📄 Uploading document: {}".format(file_path))
    
    try:
        # Verify the file exists and is readable
        if not os.path.isfile(file_path):
            print("❌ File does not exist: {}".format(file_path))
            return None, None
            
        # Check if API is available first
        try:
            health_check = requests.get(f"{API_BASE_URL}/health", timeout=5)
            print("API health check: {} ({})".format(health_check.status_code, health_check.json().get('status', 'unknown')))
            
            db_status = health_check.json().get('services', {}).get('database', 'unknown')
            if db_status != "connected":
                print("⚠️ Warning: Database appears to be disconnected, upload may fail")
        except Exception as health_e:
            print("⚠️ Warning: Could not check API health: {}".format(str(health_e)))
        
        # Prepare the multipart form data with file
        with open(file_path, 'rb') as f:
            files = {'file': f}
            data = {}
            
            if description:
                data['description'] = description
                
            # Make the API call
            print("Sending request to {}/documents/upload".format(API_BASE_URL))
            response = requests.post(
                f"{API_BASE_URL}/documents/upload",
                files=files,
                data=data,
                timeout=30  # Increased timeout
            )
            
            # Check response
            if response.status_code == 200:
                result = response.json()
                document_id = result.get('id')
                print("✅ Document uploaded successfully!")
                print("📝 Document ID: {}".format(document_id))
                print("🔄 Status: {}".format(result.get('status')))
                print("🔗 Job ID: {}".format(result.get('job_id')))
                return document_id, result.get('job_id')
            else:
                print("❌ Upload failed with status code: {}".format(response.status_code))
                print("Error: {}".format(response.text))
                return None, None
                
    except requests.exceptions.ConnectionError:
        print("❌ Connection Error: Could not connect to the API at {}".format(API_BASE_URL))
        print("   Make sure the API server is running and accessible")
        return None, None
    except Exception as e:
        print("❌ Error uploading document: {}".format(str(e)))
        import traceback
        traceback.print_exc()
        return None, None

def check_document_status(document_id):
    """Check document processing status."""
    try:
        response = requests.get(f"{API_BASE_URL}/documents/{document_id}")
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"❌ Error checking document status: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"❌ Error checking status: {str(e)}")
        return None

def check_job_status(job_id):
    """Check job processing status."""
    try:
        response = requests.get(f"{API_BASE_URL}/jobs/{job_id}")
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"❌ Error checking job status: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"❌ Error checking job status: {str(e)}")
        return None

def monitor_processing(document_id, job_id, max_checks=30):
    """Monitor document processing status."""
    print("\n🔍 Monitoring document processing...")
    print("Document ID: {}".format(document_id))
    print("Job ID: {}".format(job_id))
    print("-" * 50)
    
    checks = 0
    while checks < max_checks:
        # Get document status
        doc_status = check_document_status(document_id)
        job_status = check_job_status(job_id) if job_id else None
        
        if not doc_status:
            print("❌ Failed to get document status")
            return False
            
        status = doc_status.get('status')
        print("📊 Check #{}: Document status: {}".format(checks+1, status))
        
        if job_status:
            print("   Job status: {}".format(job_status.get('status')))
            
        # Check if processing is complete
        if status == "processed":
            print("\n✅ Document processing completed successfully!")
            print("📄 Extracted text preview:")
            extracted_text = doc_status.get('extracted_text', '')
            print("-" * 50)
            print(extracted_text[:500] + ("..." if len(extracted_text) > 500 else ""))
            print("-" * 50)
            return True
            
        elif status == "failed":
            print("\n❌ Document processing failed")
            if job_status and job_status.get('error'):
                print("Error: {}".format(job_status.get('error')))
            return False
            
        # Sleep before next check
        checks += 1
        time.sleep(POLL_INTERVAL)
        
    print("\n⏱️ Timed out waiting for processing to complete")
    return False

def main():
    """Main entry point."""
    print("🚀 Lablr Document Processing Test")
    print("=" * 50)
    
    # Check if PDF exists
    if not os.path.exists(PDF_PATH):
        print("❌ PDF file not found: {}".format(PDF_PATH))
        sys.exit(1)
        
    # Upload document
    document_id, job_id = upload_document(PDF_PATH, "Test document")
    
    if not document_id:
        print("❌ Upload failed, exiting test")
        sys.exit(1)
        
    # Monitor processing
    success = monitor_processing(document_id, job_id)
    
    if success:
        print("\n🎉 Test completed successfully!")
    else:
        print("\n⚠️ Test completed with errors")
        
    print("\n📋 Summary:")
    print("Document ID: {}".format(document_id))
    print("Job ID: {}".format(job_id))
    
if __name__ == "__main__":
    main()
