#!/usr/bin/env python3
"""
Test Azure Form Recognizer Service directly
"""

import os
import sys
from src.services.azure_form_recognizer import AzureFormRecognizerService
from src.core.config import get_settings

def test_form_recognizer():
    """Test Azure Form Recognizer with a sample PDF."""
    print("Testing Azure Form Recognizer...")
    
    # Get settings
    settings = get_settings()
    
    # Get endpoint and key from settings
    endpoint = settings.azure_form_recognizer_endpoint
    key = settings.azure_form_recognizer_key
    
    print(f"Endpoint: {endpoint}")
    print(f"Key: {key[:5]}...{key[-5:]}")
    
    # Create service
    try:
        service = AzureFormRecognizerService(
            endpoint=endpoint,
            credential=key
        )
        print("✅ Service created successfully")
    except Exception as e:
        print(f"❌ Service creation failed: {str(e)}")
        return
    
    # Test with sample PDF
    test_pdf = "test_files/test_document.pdf"
    if not os.path.exists(test_pdf):
        print(f"❌ Test PDF not found: {test_pdf}")
        return
    
    print(f"Testing with PDF: {test_pdf}")
    
    try:
        # Extract text
        print("Extracting text from PDF...")
        extracted_data = service.extract_text_from_pdf(test_pdf)
        print("✅ Text extraction successful")
        print(f"Extracted content: {extracted_data['content'][:200]}...")
        
        # Analyze document structure
        print("\nAnalyzing document structure...")
        structure_data = service.analyze_document_structure(test_pdf)
        print("✅ Structure analysis successful")
        print(f"Document has {structure_data['page_count']} page(s)")
        
        # Try key-value extraction
        print("\nExtracting key-value pairs...")
        try:
            kv_data = service.extract_key_value_pairs(test_pdf)
            print("✅ Key-value extraction successful")
            print(f"Found {len(kv_data['key_value_pairs'])} key-value pairs")
        except Exception as kv_e:
            print(f"⚠️ Key-value extraction failed: {str(kv_e)}")
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_form_recognizer()
