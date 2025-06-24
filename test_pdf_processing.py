#!/usr/bin/env python3
"""
Lablr PDF Processing Test

This script tests the complete PDF processing pipeline:
1. Upload a PDF document
2. Track the processing job until completion
3. Retrieve and display extracted content
4. Perform additional extraction operations

Usage:
    python3 test_pdf_processing.py [port] [pdf_path]
    
    - port: API server port (default: 8002)
    - pdf_path: Path to the PDF file (default: test_files/test_document.pdf)
"""

import os
import sys
import time
import json
import asyncio
import aiohttp
from pathlib import Path
from datetime import datetime

class LablrPDFTest:
    """Test the Lablr PDF processing capabilities."""
    
    def __init__(self, base_url="http://localhost:8002", pdf_path=None):
        """
        Initialize the test with the API URL and PDF path.
        
        Args:
            base_url: URL of the Lablr API server
            pdf_path: Path to the test PDF file
        """
        self.base_url = base_url
        
        if pdf_path and os.path.exists(pdf_path):
            self.pdf_path = pdf_path
        else:
            test_dir = Path.home() / "Lablr" / "test_files"
            self.pdf_path = str(test_dir / "test_document.pdf")
            if not os.path.exists(self.pdf_path):
                raise FileNotFoundError(f"PDF file not found at {self.pdf_path}")
        
        print(f"🔍 Testing with PDF: {self.pdf_path}")
    
    async def test_pdf_upload(self):
        """Upload a PDF document and return the document ID."""
        print("\n📤 Uploading PDF document...")
        
        # Prepare the file upload
        data = aiohttp.FormData()
        data.add_field('file', 
                      open(self.pdf_path, 'rb'),
                      filename=os.path.basename(self.pdf_path),
                      content_type='application/pdf')
        data.add_field('description', 'Test document for system validation')
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/documents/upload",
                    data=data
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        document_id = result.get('id')
                        job_id = result.get('job_id')
                        print(f"✅ Document uploaded successfully")
                        print(f"   Document ID: {document_id}")
                        print(f"   Job ID: {job_id}")
                        return document_id, job_id
                    else:
                        error_text = await response.text()
                        print(f"❌ Upload failed: HTTP {response.status}")
                        print(f"   Error: {error_text}")
                        return None, None
        except Exception as e:
            print(f"❌ Upload failed with exception: {str(e)}")
            return None, None
    
    async def poll_job_status(self, job_id, max_attempts=30, delay=2):
        """
        Poll job status until completion.
        
        Args:
            job_id: The job ID to track
            max_attempts: Maximum polling attempts
            delay: Delay between polling attempts in seconds
        
        Returns:
            Final job status
        """
        if not job_id:
            print("❌ No job ID provided")
            return None
        
        print(f"\n⏱️ Polling job status for job {job_id}...")
        
        for attempt in range(max_attempts):
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(
                        f"{self.base_url}/jobs/{job_id}"
                    ) as response:
                        if response.status == 200:
                            job_data = await response.json()
                            status = job_data.get('status')
                            print(f"   Attempt {attempt + 1}: Status = {status}")
                            
                            if status in ["success", "failure"]:
                                print(f"✅ Job completed with status: {status}")
                                return job_data
                            
                        else:
                            print(f"⚠️ Error fetching job status: HTTP {response.status}")
                
                await asyncio.sleep(delay)
                
            except Exception as e:
                print(f"⚠️ Error polling job status: {str(e)}")
                await asyncio.sleep(delay)
        
        print(f"⚠️ Timeout waiting for job completion")
        return None
    
    async def get_document_details(self, document_id):
        """
        Retrieve document details after processing.
        
        Args:
            document_id: Document ID
        
        Returns:
            Document details
        """
        if not document_id:
            print("❌ No document ID provided")
            return None
        
        print(f"\n📃 Retrieving document details for {document_id}...")
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/documents/{document_id}"
                ) as response:
                    if response.status == 200:
                        doc_data = await response.json()
                        print(f"✅ Document details retrieved")
                        print(f"   Status: {doc_data.get('status')}")
                        return doc_data
                    else:
                        error_text = await response.text()
                        print(f"❌ Failed to retrieve document: HTTP {response.status}")
                        print(f"   Error: {error_text}")
                        return None
        except Exception as e:
            print(f"❌ Error retrieving document details: {str(e)}")
            return None
    
    async def run_extraction(self, document_id, extraction_type="structured_data"):
        """
        Perform extraction operations on the document.
        
        Args:
            document_id: Document ID
            extraction_type: Type of extraction to perform
        
        Returns:
            Extraction results
        """
        if not document_id:
            print("❌ No document ID provided")
            return None
        
        print(f"\n🔍 Running {extraction_type} extraction for document {document_id}...")
        
        # Based on the API errors, it seems these need to be query parameters
        params = {
            "document_id": document_id,
            "extraction_type": extraction_type,
            "prompt": f"Extract all relevant information from this document using {extraction_type}.",
            "output_format": "json"
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/extraction/single",
                    params=params
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        print(f"✅ Extraction started")
                        print(f"   Task ID: {result.get('task_id')}")
                        
                        # Poll for extraction results
                        if extraction_type != "structured_data":  # For demo brevity
                            await self.poll_job_status(result.get('task_id'))
                        
                        return result
                    else:
                        error_text = await response.text()
                        print(f"❌ Extraction failed: HTTP {response.status}")
                        print(f"   Error: {error_text}")
                        return None
        except Exception as e:
            print(f"❌ Error performing extraction: {str(e)}")
            return None
    
    async def display_document_content(self, document_data):
        """Display the extracted document content."""
        if not document_data:
            return
        
        print("\n📋 Document Content:")
        print("=" * 50)
        
        # Display extracted text (truncated if too long)
        extracted_text = document_data.get("extracted_text", "")
        if extracted_text:
            if len(extracted_text) > 500:
                print(extracted_text[:500] + "... (truncated)")
            else:
                print(extracted_text)
        else:
            print("No extracted text available")
        
        print("=" * 50)
        
        # Display confidence scores if available
        confidence_scores = document_data.get("confidence_scores", {})
        if confidence_scores:
            print(f"Confidence Scores: {json.dumps(confidence_scores, indent=2)}")
    
    async def run_full_test(self):
        """Run a complete PDF processing test."""
        print("🔬 Starting Lablr PDF Processing Test")
        print("=" * 50)
        
        # Step 1: Upload the document
        document_id, job_id = await self.test_pdf_upload()
        
        if not document_id:
            print("❌ Test failed: Could not upload document")
            return False
        
        # Step 2: Poll for job completion
        job_result = await self.poll_job_status(job_id)
        
        if not job_result or job_result.get("status") != "success":
            print("❌ Test failed: Document processing did not complete successfully")
            # Continue anyway to check document status
        
        # Step 3: Get document details
        document_data = await self.get_document_details(document_id)
        
        if not document_data:
            print("❌ Test failed: Could not retrieve document details")
            return False
        
        # Step 4: Display document content
        await self.display_document_content(document_data)
        
        # Step 5: Run additional extraction operations
        extraction_result = await self.run_extraction(document_id, "structured_data")
        
        print("\n" + "=" * 50)
        print("🏁 Test Summary")
        print("=" * 50)
        
        print(f"Document ID: {document_id}")
        print(f"Processing Job ID: {job_id}")
        print(f"Document Status: {document_data.get('status')}")
        print(f"Additional Extraction: {'✅ Success' if extraction_result else '❌ Failed'}")
        print("\n🎉 PDF processing test completed!")
        
        return True

async def main():
    """Main test runner."""
    # Get port from command line
    port = 8002
    if len(sys.argv) > 1 and sys.argv[1].isdigit():
        port = int(sys.argv[1])
    
    # Get PDF path from command line
    pdf_path = None
    if len(sys.argv) > 2:
        pdf_path = sys.argv[2]
    
    tester = LablrPDFTest(base_url=f"http://localhost:{port}", pdf_path=pdf_path)
    await tester.run_full_test()

if __name__ == "__main__":
    asyncio.run(main())
