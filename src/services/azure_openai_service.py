from openai import AzureOpenAI
import json
import logging
from typing import Dict, List, Optional, Any, Union
import asyncio
from datetime import datetime
import re

logger = logging.getLogger(__name__)

class AzureOpenAIService:
    """Service for Azure OpenAI-powered document analysis and extraction."""
    
    def __init__(self, endpoint: str, api_key: str, api_version: str = "2024-02-15-preview"):
        """
        Initialize the Azure OpenAI service.
        
        Args:
            endpoint: Azure OpenAI endpoint URL
            api_key: API key for authentication
            api_version: API version to use
        """
        self.client = AzureOpenAI(
            azure_endpoint=endpoint,
            api_key=api_key,
            api_version=api_version
        )
        self.endpoint = endpoint
        
    def extract_structured_data(
        self, 
        document_text: str, 
        extraction_prompt: str,
        custom_fields: Optional[Dict[str, str]] = None,
        model: str = "gpt-4"
    ) -> Dict[str, Any]:
        """
        Extract structured data from document text using a custom prompt.
        
        Args:
            document_text: The text content of the document
            extraction_prompt: User-defined prompt describing what to extract
            custom_fields: Optional custom field definitions
            model: Azure OpenAI model to use
            
        Returns:
            Extracted structured data
        """
        try:
            # Build the system prompt
            system_prompt = self._build_system_prompt(extraction_prompt, custom_fields)
            
            # Prepare the user message
            user_message = f"""
            Please analyze the following document and extract the requested information:

            DOCUMENT TEXT:
            {document_text}

            EXTRACTION REQUIREMENTS:
            {extraction_prompt}

            Please provide the extracted data in valid JSON format.
            """
            
            # Call Azure OpenAI
            response = self.client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                temperature=0.1,
                max_tokens=4000,
                response_format={"type": "json_object"}
            )
            
            # Parse the response
            extracted_data = json.loads(response.choices[0].message.content)
            
            # Add metadata
            result = {
                "extracted_data": extracted_data,
                "model_used": model,
                "timestamp": datetime.utcnow().isoformat(),
                "token_usage": {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                }
            }
            
            logger.info(f"Successfully extracted structured data using {model}")
            return result
            
        except Exception as e:
            logger.error(f"Error extracting structured data: {str(e)}")
            raise
    
    def generate_qa_pairs(
        self, 
        document_text: str, 
        qa_prompt: str,
        num_questions: int = 10,
        model: str = "gpt-4"
    ) -> List[Dict[str, str]]:
        """
        Generate Q&A pairs from document text.
        
        Args:
            document_text: The text content of the document
            qa_prompt: Prompt describing what kind of Q&A pairs to generate
            num_questions: Number of Q&A pairs to generate
            model: Azure OpenAI model to use
            
        Returns:
            List of Q&A pairs
        """
        try:
            system_prompt = f"""
            You are an expert at creating question-answer pairs for training AI models.
            Generate {num_questions} high-quality question-answer pairs based on the document content.
            
            Guidelines:
            - Questions should be clear, specific, and answerable from the document
            - Answers should be accurate and concise
            - Include a mix of factual, analytical, and inferential questions
            - Return the result as a JSON array of objects with 'question' and 'answer' fields
            
            Specific requirements: {qa_prompt}
            """
            
            user_message = f"""
            Generate {num_questions} question-answer pairs from this document:

            DOCUMENT TEXT:
            {document_text}

            Return as JSON array format: [{"question": "...", "answer": "..."}, ...]
            """
            
            response = self.client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                temperature=0.3,
                max_tokens=4000,
                response_format={"type": "json_object"}
            )
            
            # Parse the response
            result = json.loads(response.choices[0].message.content)
            qa_pairs = result.get("qa_pairs", result.get("questions", []))
            
            logger.info(f"Generated {len(qa_pairs)} Q&A pairs")
            return qa_pairs
            
        except Exception as e:
            logger.error(f"Error generating Q&A pairs: {str(e)}")
            raise
    
    def summarize_document(
        self, 
        document_text: str, 
        summary_prompt: str,
        model: str = "gpt-4"
    ) -> Dict[str, str]:
        """
        Summarize document content based on custom prompt.
        
        Args:
            document_text: The text content of the document
            summary_prompt: Prompt describing how to summarize
            model: Azure OpenAI model to use
            
        Returns:
            Summary information
        """
        try:
            system_prompt = f"""
            You are an expert document summarizer. Create a summary based on the specific requirements provided.
            
            Summary requirements: {summary_prompt}
            
            Provide the summary in JSON format with appropriate fields.
            """
            
            user_message = f"""
            Please summarize the following document according to the requirements:

            DOCUMENT TEXT:
            {document_text}
            """
            
            response = self.client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                temperature=0.2,
                max_tokens=2000,
                response_format={"type": "json_object"}
            )
            
            summary = json.loads(response.choices[0].message.content)
            
            logger.info("Successfully generated document summary")
            return summary
            
        except Exception as e:
            logger.error(f"Error summarizing document: {str(e)}")
            raise
    
    def extract_entities(
        self, 
        document_text: str, 
        entity_prompt: str,
        model: str = "gpt-4"
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Extract named entities from document text.
        
        Args:
            document_text: The text content of the document
            entity_prompt: Prompt describing what entities to extract
            model: Azure OpenAI model to use
            
        Returns:
            Extracted entities organized by type
        """
        try:
            system_prompt = f"""
            You are an expert at named entity recognition and extraction.
            Extract entities from the document based on the specified requirements.
            
            Entity extraction requirements: {entity_prompt}
            
            Return the results in JSON format with entities grouped by type.
            Include confidence scores and source text references where possible.
            """
            
            user_message = f"""
            Extract entities from this document:

            DOCUMENT TEXT:
            {document_text}
            
            Return as JSON with entity types as keys and arrays of entity objects as values.
            Each entity should have: "text", "type", "confidence", "context"
            """
            
            response = self.client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                temperature=0.1,
                max_tokens=3000,
                response_format={"type": "json_object"}
            )
            
            entities = json.loads(response.choices[0].message.content)
            
            logger.info("Successfully extracted entities")
            return entities
            
        except Exception as e:
            logger.error(f"Error extracting entities: {str(e)}")
            raise
    
    def classify_document(
        self, 
        document_text: str, 
        classification_prompt: str,
        model: str = "gpt-4"
    ) -> Dict[str, Any]:
        """
        Classify document based on custom criteria.
        
        Args:
            document_text: The text content of the document
            classification_prompt: Prompt describing classification criteria
            model: Azure OpenAI model to use
            
        Returns:
            Classification results with confidence scores
        """
        try:
            system_prompt = f"""
            You are an expert document classifier. Classify the document based on the provided criteria.
            
            Classification requirements: {classification_prompt}
            
            Provide classification results in JSON format with confidence scores and reasoning.
            """
            
            user_message = f"""
            Classify this document:

            DOCUMENT TEXT:
            {document_text}
            
            Provide results in JSON format with: "classification", "confidence", "reasoning", "subcategories"
            """
            
            response = self.client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                temperature=0.1,
                max_tokens=1500,
                response_format={"type": "json_object"}
            )
            
            classification = json.loads(response.choices[0].message.content)
            
            logger.info("Successfully classified document")
            return classification
            
        except Exception as e:
            logger.error(f"Error classifying document: {str(e)}")
            raise
    
    def _build_system_prompt(self, extraction_prompt: str, custom_fields: Optional[Dict[str, str]] = None) -> str:
        """Build the system prompt for structured data extraction."""
        
        base_prompt = """
        You are an expert at extracting structured data from documents.
        Follow these guidelines:
        1. Extract only the information that is explicitly present in the document
        2. If information is not available, use null or indicate "not found"
        3. Maintain data types (numbers as numbers, dates as dates, etc.)
        4. Be precise and accurate
        5. Return data in valid JSON format
        """
        
        if custom_fields:
            field_definitions = "\n".join([
                f"- {field}: {description}" 
                for field, description in custom_fields.items()
            ])
            base_prompt += f"\n\nCustom field definitions:\n{field_definitions}"
        
        base_prompt += f"\n\nExtraction task: {extraction_prompt}"
        
        return base_prompt
    
    async def process_batch_async(
        self, 
        documents: List[Dict[str, str]], 
        extraction_prompt: str,
        extraction_type: str = "structured_data",
        **kwargs
    ) -> List[Dict[str, Any]]:
        """
        Process multiple documents asynchronously.
        
        Args:
            documents: List of documents with 'id' and 'text' fields
            extraction_prompt: Extraction prompt
            extraction_type: Type of extraction to perform
            **kwargs: Additional arguments for specific extraction methods
            
        Returns:
            List of extraction results
        """
        tasks = []
        
        for doc in documents:
            if extraction_type == "structured_data":
                task = asyncio.create_task(
                    self._extract_structured_data_async(doc, extraction_prompt, **kwargs)
                )
            elif extraction_type == "qa_generation":
                task = asyncio.create_task(
                    self._generate_qa_pairs_async(doc, extraction_prompt, **kwargs)
                )
            elif extraction_type == "summarization":
                task = asyncio.create_task(
                    self._summarize_document_async(doc, extraction_prompt, **kwargs)
                )
            elif extraction_type == "entity_extraction":
                task = asyncio.create_task(
                    self._extract_entities_async(doc, extraction_prompt, **kwargs)
                )
            elif extraction_type == "classification":
                task = asyncio.create_task(
                    self._classify_document_async(doc, extraction_prompt, **kwargs)
                )
            else:
                task = asyncio.create_task(
                    self._extract_structured_data_async(doc, extraction_prompt, **kwargs)
                )
            
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results and handle exceptions
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append({
                    "document_id": documents[i]["id"],
                    "status": "error",
                    "error": str(result)
                })
            else:
                processed_results.append({
                    "document_id": documents[i]["id"],
                    "status": "success",
                    "result": result
                })
        
        return processed_results
    
    async def _extract_structured_data_async(self, document: Dict[str, str], prompt: str, **kwargs):
        """Async wrapper for structured data extraction."""
        return await asyncio.to_thread(
            self.extract_structured_data,
            document["text"],
            prompt,
            **kwargs
        )
    
    async def _generate_qa_pairs_async(self, document: Dict[str, str], prompt: str, **kwargs):
        """Async wrapper for Q&A generation."""
        return await asyncio.to_thread(
            self.generate_qa_pairs,
            document["text"],
            prompt,
            **kwargs
        )
    
    async def _summarize_document_async(self, document: Dict[str, str], prompt: str, **kwargs):
        """Async wrapper for document summarization."""
        return await asyncio.to_thread(
            self.summarize_document,
            document["text"],
            prompt,
            **kwargs
        )
    
    async def _extract_entities_async(self, document: Dict[str, str], prompt: str, **kwargs):
        """Async wrapper for entity extraction."""
        return await asyncio.to_thread(
            self.extract_entities,
            document["text"],
            prompt,
            **kwargs
        )
    
    async def _classify_document_async(self, document: Dict[str, str], prompt: str, **kwargs):
        """Async wrapper for document classification."""
        return await asyncio.to_thread(
            self.classify_document,
            document["text"],
            prompt,
            **kwargs
        ) 