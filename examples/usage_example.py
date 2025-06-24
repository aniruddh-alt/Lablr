"""
Example usage of the Lablr PDF Data Labeling System.

This script demonstrates how to:
1. Upload PDFs
2. Create extraction jobs with custom prompts
3. Monitor job progress
4. Download results in various formats

Prerequisites:
- Azure services configured (Form Recognizer, OpenAI)
- Lablr API running on localhost:8000
- Redis and Celery workers running
"""

import asyncio
import aiohttp
import json
from pathlib import Path
import time

class LablrClient:
    """Simple client for interacting with the Lablr API."""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
    
    async def upload_document(self, file_path: str, description: str = None) -> dict:
        """Upload a single PDF document."""
        url = f"{self.base_url}/documents/upload"
        
        with open(file_path, 'rb') as f:
            data = aiohttp.FormData()
            data.add_field('file', f, filename=Path(file_path).name, content_type='application/pdf')
            if description:
                data.add_field('description', description)
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, data=data) as response:
                    return await response.json()
    
    async def create_extraction_job(self, job_config: dict) -> dict:
        """Create a new extraction job."""
        url = f"{self.base_url}/extraction/jobs"
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=job_config) as response:
                return await response.json()

# Example extraction prompts for different use cases
EXTRACTION_PROMPTS = {
    "invoice_data": {
        "name": "Invoice Data Extraction",
        "description": "Extract key information from invoices for accounting",
        "extraction_type": "structured_data",
        "output_format": "csv",
        "prompt": """
        Extract the following information from each invoice:
        - company_name: The name of the company issuing the invoice
        - invoice_number: The unique invoice identifier
        - invoice_date: The date the invoice was issued (YYYY-MM-DD format)
        - due_date: The payment due date (YYYY-MM-DD format)
        - total_amount: The total amount due (numeric value only)
        - tax_amount: The tax amount (numeric value only)
        - currency: The currency code (e.g., USD, EUR)
        - customer_name: The name of the customer/client
        - line_items: Array of items with description and amount
        
        If any field is not found, use null.
        """,
        "custom_fields": {
            "company_name": "The business name on the invoice header",
            "invoice_number": "Unique identifier for tracking",
            "total_amount": "Final amount due including all charges",
            "line_items": "Individual products or services listed"
        }
    }
}

def print_usage_instructions():
    """Print instructions for using the system."""
    print("""
=== Lablr PDF Data Labeling System Usage Guide ===

1. SETUP:
   - Configure Azure services in environment variables:
     * AZURE_FORM_RECOGNIZER_ENDPOINT
     * AZURE_FORM_RECOGNIZER_KEY
     * AZURE_OPENAI_ENDPOINT
     * AZURE_OPENAI_KEY

2. BASIC WORKFLOW:
   a) Upload PDFs (single or bulk)
   b) Create extraction job with custom prompt
   c) Monitor progress
   d) Download results in desired format

3. SUPPORTED EXTRACTION TYPES:
   - structured_data: Extract specific fields into structured format
   - qa_generation: Generate question-answer pairs for training
   - summarization: Create summaries based on custom requirements
   - classification: Classify documents and extract metadata
   - entity_extraction: Find named entities (people, organizations, etc.)

4. OUTPUT FORMATS:
   - CSV: For machine learning datasets
   - JSON/JSONL: For API integration
   - Excel: For business reporting
   - Markdown: For documentation
   - QA Pairs: For training AI models
""")

async def main():
    """Run example usage scenarios."""
    print_usage_instructions()
    print("\nExample system ready for use!")

if __name__ == "__main__":
    asyncio.run(main())
