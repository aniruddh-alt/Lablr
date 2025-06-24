# Lablr - AI-Powered PDF Data Labeling System

Lablr is a comprehensive data labeling solution that uses Azure AI services to extract, process, and transform data from PDF documents into structured formats suitable for machine learning, business intelligence, and AI training.

## 🎯 Features

### Core Capabilities
- **Multi-PDF Processing**: Upload and process single PDFs or batches of documents
- **Custom Prompt-Based Extraction**: Define exactly what data to extract using natural language prompts
- **Multiple Extraction Types**: 
  - Structured data extraction (forms, invoices, contracts)
  - Q&A pair generation for AI training
  - Document summarization
  - Named entity recognition
  - Document classification
- **Multiple Output Formats**: CSV, JSON, JSONL, Excel, Markdown, Q&A pairs
- **Real-time Processing**: Background job processing with progress monitoring
- **Azure Integration**: Leverages Azure Form Recognizer and Azure OpenAI

### Use Cases
- **Invoice Processing**: Extract accounting data from invoices
- **Contract Analysis**: Parse legal documents and extract key terms
- **Research Paper Processing**: Generate Q&A pairs for AI training
- **Document Classification**: Automatically categorize document types
- **Business Intelligence**: Convert unstructured documents to structured data

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   FastAPI Web   │    │   Celery        │    │   Azure AI      │
│   Application   │◄──►│   Workers       │◄──►│   Services      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   File Storage  │    │   Redis Queue   │    │   Output Files  │
│   (uploads/)    │    │   & Cache       │    │   (outputs/)    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 🚀 Quick Start

### Prerequisites

1. **Azure Services**:
   - Azure Form Recognizer resource
   - Azure OpenAI service with GPT-4 deployment
   
2. **System Requirements**:
   - Python 3.8+
   - Redis server
   - PostgreSQL (optional, for production)

### Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd Lablr
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**:
   ```bash
   # Create .env file
   AZURE_FORM_RECOGNIZER_ENDPOINT=https://your-resource.cognitiveservices.azure.com/
   AZURE_FORM_RECOGNIZER_KEY=your_form_recognizer_key
   AZURE_OPENAI_ENDPOINT=https://your-openai.openai.azure.com/
   AZURE_OPENAI_KEY=your_openai_key
   AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4
   REDIS_URL=redis://localhost:6379
   ```

4. **Start Redis**:
   ```bash
   redis-server
   ```

5. **Start Celery worker**:
   ```bash
   celery -A src.workers.celery_app worker --loglevel=info
   ```

6. **Start the API server**:
   ```bash
   python -m src.api.main
   ```

7. **Access the application**:
   - API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs

## 📖 Usage Examples

### 1. Invoice Data Extraction

```python
import asyncio
from examples.usage_example import LablrClient

async def extract_invoice_data():
    client = LablrClient()
    
    # Upload invoices
    upload_result = await client.upload_documents_bulk([
        "invoices/invoice_001.pdf",
        "invoices/invoice_002.pdf"
    ])
    
    # Create extraction job
    job_config = {
        "name": "Invoice Processing",
        "document_ids": [doc["document_id"] for doc in upload_result["results"]],
        "extraction_type": "structured_data",
        "output_format": "csv",
        "prompt": """
        Extract the following from each invoice:
        - company_name: Name of the issuing company
        - invoice_number: Unique invoice ID
        - total_amount: Final amount due
        - invoice_date: Date issued (YYYY-MM-DD)
        - line_items: List of products/services
        """,
        "custom_fields": {
            "company_name": "The business name in the header",
            "total_amount": "Final amount including tax"
        }
    }
    
    job = await client.create_extraction_job(job_config)
    print(f"Created job: {job['id']}")

# Run the example
asyncio.run(extract_invoice_data())
```

## 🔧 API Reference

### Document Upload Endpoints

- `POST /documents/upload` - Upload single PDF
- `POST /documents/upload/bulk` - Upload multiple PDFs
- `GET /documents` - List uploaded documents
- `GET /documents/{id}` - Get document details

### Extraction Job Endpoints

- `POST /extraction/jobs` - Create extraction job
- `GET /extraction/jobs` - List extraction jobs
- `GET /extraction/jobs/{id}` - Get job details
- `GET /extraction/jobs/{id}/status` - Get job progress
- `GET /extraction/jobs/{id}/download` - Download results

## 📊 Output Formats

### CSV Format
Perfect for machine learning datasets and business analysis:
```csv
document_id,company_name,invoice_number,total_amount,invoice_date
doc1,Acme Corp,INV-001,1250.00,2024-01-15
doc2,Tech Solutions,INV-002,890.50,2024-01-16
```

### JSON Format
Ideal for API integration and programmatic access:
```json
{
  "job_name": "Invoice Processing",
  "results": [
    {
      "document_id": "doc1",
      "extracted_data": {
        "company_name": "Acme Corp",
        "invoice_number": "INV-001",
        "total_amount": 1250.00
      }
    }
  ]
}
```

## ⚙️ Configuration

### Environment Variables

```bash
# Azure Services
AZURE_FORM_RECOGNIZER_ENDPOINT=https://your-resource.cognitiveservices.azure.com/
AZURE_FORM_RECOGNIZER_KEY=your_key
AZURE_OPENAI_ENDPOINT=https://your-openai.openai.azure.com/
AZURE_OPENAI_KEY=your_key
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4

# Database
DATABASE_URL=postgresql://user:pass@localhost/lablr
REDIS_URL=redis://localhost:6379

# Application
SECRET_KEY=your-secret-key
MAX_FILE_SIZE=52428800  # 50MB
MAX_CONCURRENT_JOBS=10
```

## 📄 License

This project is licensed under the MIT License.

## 🆘 Support

- **Documentation**: Check the `/docs` endpoint when running the API
- **Issues**: Report bugs and request features via GitHub Issues
- **Examples**: See the `examples/` directory for usage patterns

---

**Lablr** - Transform your PDFs into structured data with the power of Azure AI! 🚀 - AI-Powered PDF Data Labeling System

Lablr is a comprehensive data labeling solution that uses Azure AI services to extract, process, and transform data from PDF documents into structured formats suitable for machine learning, business intelligence, and AI training.

## 🎯 Features

### Core Capabilities
- **Multi-PDF Processing**: Upload and process single PDFs or batches of documents
- **Custom Prompt-Based Extraction**: Define exactly what data to extract using natural language prompts
- **Multiple Extraction Types**: 
  - Structured data extraction (forms, invoices, contracts)
  - Q&A pair generation for AI training
  - Document summarization
  - Named entity recognition
  - Document classification
- **Multiple Output Formats**: CSV, JSON, JSONL, Excel, Markdown, Q&A pairs
- **Real-time Processing**: Background job processing with progress monitoring
- **Azure Integration**: Leverages Azure Form Recognizer and Azure OpenAI

### Use Cases
- **Invoice Processing**: Extract accounting data from invoices
- **Contract Analysis**: Parse legal documents and extract key terms
- **Research Paper Processing**: Generate Q&A pairs for AI training
- **Document Classification**: Automatically categorize document types
- **Business Intelligence**: Convert unstructured documents to structured data

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   FastAPI Web   │    │   Celery        │    │   Azure AI      │
│   Application   │◄──►│   Workers       │◄──►│   Services      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   File Storage  │    │   Redis Queue   │    │   Output Files  │
│   (uploads/)    │    │   & Cache       │    │   (outputs/)    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 🚀 Quick Start

### Prerequisites

1. **Azure Services**:
   - Azure Form Recognizer resource
   - Azure OpenAI service with GPT-4 deployment
   
2. **System Requirements**:
   - Python 3.8+
   - Redis server
   - PostgreSQL (optional, for production)

### Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd Lablr
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**:
   ```bash
   # Create .env file
   AZURE_FORM_RECOGNIZER_ENDPOINT=https://your-resource.cognitiveservices.azure.com/
   AZURE_FORM_RECOGNIZER_KEY=your_form_recognizer_key
   AZURE_OPENAI_ENDPOINT=https://your-openai.openai.azure.com/
   AZURE_OPENAI_KEY=your_openai_key
   AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4
   REDIS_URL=redis://localhost:6379
   ```

4. **Start Redis**:
   ```bash
   redis-server
   ```

5. **Start Celery worker**:
   ```bash
   celery -A src.workers.celery_app worker --loglevel=info
   ```

6. **Start the API server**:
   ```bash
   python -m src.api.main
   ```

7. **Access the application**:
   - API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs

## 📖 Usage Examples

### 1. Invoice Data Extraction

```python
import asyncio
from examples.usage_example import LablrClient

async def extract_invoice_data():
    client = LablrClient()
    
    # Upload invoices
    upload_result = await client.upload_documents_bulk([
        "invoices/invoice_001.pdf",
        "invoices/invoice_002.pdf"
    ])
    
    # Create extraction job
    job_config = {
        "name": "Invoice Processing",
        "document_ids": [doc["document_id"] for doc in upload_result["results"]],
        "extraction_type": "structured_data",
        "output_format": "csv",
        "prompt": """
        Extract the following from each invoice:
        - company_name: Name of the issuing company
        - invoice_number: Unique invoice ID
        - total_amount: Final amount due
        - invoice_date: Date issued (YYYY-MM-DD)
        - line_items: List of products/services
        """,
        "custom_fields": {
            "company_name": "The business name in the header",
            "total_amount": "Final amount including tax"
        }
    }
    
    job = await client.create_extraction_job(job_config)
    print(f"Created job: {job['id']}")

# Run the example
asyncio.run(extract_invoice_data())
```

### 2. Q&A Pair Generation

```python
async def generate_qa_pairs():
    client = LablrClient()
    
    job_config = {
        "name": "Research Paper Q&A",
        "document_ids": ["research_paper_1", "research_paper_2"],
        "extraction_type": "qa_generation",
        "output_format": "qa_pairs",
        "prompt": """
        Generate educational Q&A pairs covering:
        - Research methodology
        - Key findings and results
        - Conclusions and implications
        - Technical concepts explained
        """,
        "num_questions": 20
    }
    
    job = await client.create_extraction_job(job_config)
    print(f"Q&A generation job: {job['id']}")
```

### 3. Document Classification

```python
async def classify_documents():
    client = LablrClient()
    
    job_config = {
        "name": "Document Classification",
        "document_ids": ["mixed_doc_1", "mixed_doc_2", "mixed_doc_3"],
        "extraction_type": "classification",
        "output_format": "csv",
        "prompt": """
        Classify each document as:
        - invoice, contract, report, manual, legal_document, or other
        
        Provide confidence score and key identifying features.
        """
    }
    
    job = await client.create_extraction_job(job_config)
```

## 🔧 API Reference

### Document Upload Endpoints

- `POST /documents/upload` - Upload single PDF
- `POST /documents/upload/bulk` - Upload multiple PDFs
- `GET /documents` - List uploaded documents
- `GET /documents/{id}` - Get document details

### Extraction Job Endpoints

- `POST /extraction/jobs` - Create extraction job
- `GET /extraction/jobs` - List extraction jobs
- `GET /extraction/jobs/{id}` - Get job details
- `GET /extraction/jobs/{id}/status` - Get job progress
- `GET /extraction/jobs/{id}/download` - Download results

### Job Management

- `GET /jobs/{id}` - Get Celery job status
- `GET /health` - System health check

## 📊 Output Formats

### CSV Format
Perfect for machine learning datasets and business analysis:
```csv
document_id,company_name,invoice_number,total_amount,invoice_date
doc1,Acme Corp,INV-001,1250.00,2024-01-15
doc2,Tech Solutions,INV-002,890.50,2024-01-16
```

### JSON Format
Ideal for API integration and programmatic access:
```json
{
  "job_name": "Invoice Processing",
  "results": [
    {
      "document_id": "doc1",
      "extracted_data": {
        "company_name": "Acme Corp",
        "invoice_number": "INV-001",
        "total_amount": 1250.00
      }
    }
  ]
}
```

### Q&A Pairs Format
Optimized for AI model training:
```json
{
  "qa_pairs": [
    {
      "question": "What is the main research objective?",
      "answer": "To evaluate the effectiveness of...",
      "document_id": "research_doc1"
    }
  ]
}
```

## 🔬 Extraction Types

### 1. Structured Data Extraction
Extract specific fields into organized data structures.

**Use Cases**: Forms, invoices, contracts, applications
**Output**: Tables with named columns and typed data

### 2. Q&A Generation  
Create question-answer pairs for training AI models.

**Use Cases**: Educational content, documentation, research papers
**Output**: Training datasets for language models

### 3. Document Summarization
Generate custom summaries based on specific requirements.

**Use Cases**: Executive summaries, abstract generation, key points extraction
**Output**: Structured summaries with key information

### 4. Named Entity Recognition
Identify and categorize important entities in documents.

**Use Cases**: Contact extraction, company identification, location mapping
**Output**: Categorized lists of entities with context

### 5. Document Classification
Automatically categorize documents by type and content.

**Use Cases**: Document routing, automated filing, content organization
**Output**: Classification labels with confidence scores

## ⚙️ Configuration

### Environment Variables

```bash
# Azure Services
AZURE_FORM_RECOGNIZER_ENDPOINT=https://your-resource.cognitiveservices.azure.com/
AZURE_FORM_RECOGNIZER_KEY=your_key
AZURE_OPENAI_ENDPOINT=https://your-openai.openai.azure.com/
AZURE_OPENAI_KEY=your_key
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4

# Database
DATABASE_URL=postgresql://user:pass@localhost/lablr
REDIS_URL=redis://localhost:6379

# Application
SECRET_KEY=your-secret-key
MAX_FILE_SIZE=52428800  # 50MB
MAX_CONCURRENT_JOBS=10
```

### Advanced Configuration

```python
# src/core/config.py
class Settings(BaseSettings):
    # Processing settings
    max_concurrent_jobs: int = 10
    job_timeout: int = 3600  # 1 hour
    batch_size: int = 5
    
    # File handling
    max_file_size: int = 50 * 1024 * 1024  # 50MB
    upload_dir: str = "uploads"
    output_dir: str = "outputs"
    
    # Azure AI settings
    azure_openai_api_version: str = "2024-02-15-preview"
    azure_openai_deployment_name: str = "gpt-4"
```

## 🚀 Deployment

### Docker Deployment

1. **Build and run with Docker Compose**:
   ```bash
   docker-compose up -d
   ```

2. **Environment configuration**:
   ```yaml
   # docker-compose.yml
   version: '3.8'
   services:
     api:
       build: .
       ports:
         - "8000:8000"
       environment:
         - AZURE_FORM_RECOGNIZER_ENDPOINT=${AZURE_FORM_RECOGNIZER_ENDPOINT}
         - AZURE_OPENAI_ENDPOINT=${AZURE_OPENAI_ENDPOINT}
     
     worker:
       build: .
       command: celery -A src.workers.celery_app worker --loglevel=info
       
     redis:
       image: redis:7-alpine
       ports:
         - "6379:6379"
   ```

### Azure Container Apps Deployment

```bash
# Deploy to Azure Container Apps
az containerapp create \
  --name lablr-api \
  --resource-group your-rg \
  --image your-registry/lablr:latest \
  --environment lablr-env \
  --env-vars AZURE_FORM_RECOGNIZER_ENDPOINT=$FORM_RECOGNIZER_ENDPOINT
```

## 🔍 Monitoring & Troubleshooting

### Health Checks
- `GET /health` - System health status
- Monitor Celery worker status
- Check Redis connectivity
- Verify Azure service availability

### Common Issues

1. **Azure Service Authentication**:
   ```
   Error: Azure credentials not configured
   Solution: Verify AZURE_*_ENDPOINT and AZURE_*_KEY variables
   ```

2. **File Upload Failures**:
   ```
   Error: File too large
   Solution: Check MAX_FILE_SIZE setting and file permissions
   ```

3. **Job Processing Errors**:
   ```
   Error: Task timeout
   Solution: Increase JOB_TIMEOUT or reduce batch size
   ```

### Logging
```python
# Configure logging level
import logging
logging.basicConfig(level=logging.INFO)

# Monitor job progress
logger = logging.getLogger(__name__)
logger.info(f"Processing document {doc_id}")
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/new-feature`
3. Make changes and test thoroughly
4. Submit a pull request with detailed description

### Development Setup

```bash
# Install development dependencies
pip install -r requirements.txt
pip install -e .

# Run tests
pytest tests/

# Code formatting
black src/
flake8 src/
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- **Documentation**: Check the `/docs` endpoint when running the API
- **Issues**: Report bugs and request features via GitHub Issues
- **Examples**: See the `examples/` directory for usage patterns

## 🔮 Roadmap

- [ ] Database integration for persistent storage
- [ ] Web UI for non-technical users
- [ ] Additional Azure AI service integrations
- [ ] Batch processing optimizations
- [ ] Advanced prompt templates
- [ ] Multi-language support
- [ ] Integration with popular ML frameworks

---

**Lablr** - Transform your PDFs into structured data with the power of Azure AI! 🚀