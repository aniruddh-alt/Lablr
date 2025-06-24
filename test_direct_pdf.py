#!/usr/bin/env python3
"""
Test PDF Upload and Processing
This script tests the entire PDF processing pipeline in a single run.
"""

import os
import sys
import json
import time
import requests
from pathlib import Path
from datetime import datetime
import traceback

def test_pdf_upload_and_processing():
    """Test PDF upload and processing workflow."""
    print("🔬 Testing PDF Upload and Processing")
    print("=" * 50)
    
    # API endpoint
    base_url = "http://localhost:8002"
    
    # Test file
    test_pdf_path = "test_files/test_document.pdf"
    if not os.path.exists(test_pdf_path):
        print(f"❌ Test PDF not found: {test_pdf_path}")
        return False
        
    print(f"📄 Using test PDF: {test_pdf_path}")
    
    # Step 1: Upload the PDF
    print("\n📤 Uploading PDF...")
    try:
        with open(test_pdf_path, 'rb') as pdf_file:
            files = {'file': (os.path.basename(test_pdf_path), pdf_file, 'application/pdf')}
            data = {'description': 'Test document for direct processing test'}
            
            response = requests.post(
                f"{base_url}/documents/upload",
                files=files,
                data=data
            )
            
        if response.status_code != 200:
            print(f"❌ Upload failed: HTTP {response.status_code}")
            print(f"Error: {response.text}")
            return False
            
        # Parse response
        result = response.json()
        document_id = result.get('id')
        job_id = result.get('job_id')
        
        print(f"✅ Upload successful")
        print(f"Document ID: {document_id}")
        print(f"Job ID: {job_id}")
        
    except Exception as e:
        print(f"❌ Upload failed with exception: {str(e)}")
        traceback.print_exc()
        return False
    
    # Step 2: Poll job status until completion
    print("\n⏱️ Monitoring job progress...")
    max_polls = 30
    poll_interval = 3  # seconds
    
    job_completed = False
    job_result = None
    
    for i in range(max_polls):
        try:
            job_response = requests.get(f"{base_url}/jobs/{job_id}")
            
            if job_response.status_code != 200:
                print(f"⚠️ Error checking job status: HTTP {job_response.status_code}")
                print(f"Error: {job_response.text}")
                time.sleep(poll_interval)
                continue
                
            job_data = job_response.json()
            status = job_data.get('status')
            
            print(f"Poll {i+1}/{max_polls}: Status = {status}")
            
            if status in ['success', 'failure']:
                job_completed = True
                job_result = job_data
                break
                
            time.sleep(poll_interval)
            
        except Exception as e:
            print(f"⚠️ Error polling job: {str(e)}")
            time.sleep(poll_interval)
    
    if not job_completed:
        print("⚠️ Job did not complete within timeout period")
    elif job_result.get('status') == 'success':
        print("✅ Job completed successfully")
    else:
        print(f"❌ Job failed: {job_result.get('error', 'Unknown error')}")
    
    # Step 3: Get document details
    print("\n📄 Retrieving document details...")
    try:
        doc_response = requests.get(f"{base_url}/documents/{document_id}")
        
        if doc_response.status_code != 200:
            print(f"❌ Failed to get document: HTTP {doc_response.status_code}")
            print(f"Error: {doc_response.text}")
        else:
            doc_data = doc_response.json()
            print(f"✅ Document retrieved")
            print(f"Status: {doc_data.get('status')}")
            
            # Display extracted text
            text = doc_data.get('extracted_text')
            if text:
                print("\n📝 Extracted Text:")
                print("-" * 50)
                print(text[:500] + ("..." if len(text) > 500 else ""))
                print("-" * 50)
            else:
                print("\n⚠️ No extracted text found")
                
    except Exception as e:
        print(f"❌ Error retrieving document: {str(e)}")
    
    # Step 4: Try an additional extraction
    print("\n🔍 Testing structured data extraction...")
    try:
        # Query parameters for the extraction
        params = {
            'document_id': document_id,
            'extraction_type': 'structured_data',
            'prompt': 'Extract all relevant information from this document.',
            'output_format': 'json'
        }
        
        extract_response = requests.post(
            f"{base_url}/extraction/single",
            params=params
        )
        
        if extract_response.status_code != 200:
            print(f"❌ Extraction request failed: HTTP {extract_response.status_code}")
            print(f"Error: {extract_response.text}")
        else:
            extract_result = extract_response.json()
            print(f"✅ Extraction started")
            print(f"Task ID: {extract_result.get('task_id')}")
            
    except Exception as e:
        print(f"❌ Error requesting extraction: {str(e)}")
    
    print("\n" + "=" * 50)
    print("🏁 Test Completed")
    
    return True

if __name__ == "__main__":
    # Install dependencies if needed
    try:
        import requests
    except ImportError:
        print("Installing required packages...")
        os.system("pip install requests")
        import requests
        
    test_pdf_upload_and_processing()
