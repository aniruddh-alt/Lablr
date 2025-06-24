from openai import AzureOpenAI
import logging
import json
from typing import Dict, List, Optional, Any, Union
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
            # Build system prompt for structured data extraction
            system_prompt = self._build_system_prompt(extraction_prompt, custom_fields)
            
            # Truncate document if needed to fit context window
            trimmed_text = self._trim_document_for_context(document_text)
            
            # Make API call to Azure OpenAI
            response = self.client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Document content:\n\n{trimmed_text}"}
                ],
                temperature=0.3,  # Low temperature for more deterministic output
                response_format={"type": "json_object"}  # Request JSON
            )
            
            # Parse the JSON response
            result_text = response.choices[0].message.content
            try:
                extracted_data = json.loads(result_text)
                logger.debug("Successfully parsed JSON response")
            except json.JSONDecodeError:
                logger.warning("Failed to parse response as JSON, returning raw text")
                extracted_data = {"raw_text": result_text}
            
            # Add metadata to response
            result = {
                "extracted_data": extracted_data,
                "model_used": model,
                "extraction_prompt": extraction_prompt,
                "processed_at": datetime.utcnow().isoformat(),
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
            return {
                "error": str(e),
                "processed_at": datetime.utcnow().isoformat(),
                "model_used": model,
                "extraction_prompt": extraction_prompt,
                "status": "failed"
            }
    
    def generate_qa_pairs(
        self, 
        document_text: str, 
        qa_prompt: str,
        num_questions: int = 10,
        model: str = "gpt-4"
    ) -> Dict[str, Any]:
        """
        Generate Q&A pairs from document text.
        
        Args:
            document_text: The text content of the document
            qa_prompt: Prompt describing what kind of Q&A pairs to generate
            num_questions: Number of questions to generate
            model: Azure OpenAI model to use
            
        Returns:
            Dictionary containing Q&A pairs and metadata
        """
        try:
            # Trim document if needed
            trimmed_text = self._trim_document_for_context(document_text)
            
            # Build system prompt for Q&A generation
            system_prompt = f"""
            You are an expert Q&A generation system. Your task is to generate {num_questions} high-quality question and answer pairs 
            from a document. These Q&A pairs should:
            
            1. Cover important information in the document
            2. Be diverse and explore different aspects of the content
            3. Include factual information that can be directly verified from the text
            4. Range from simple to complex questions
            
            {qa_prompt}
            
            Format your response as a valid JSON array with objects containing 'question' and 'answer' fields.
            """
            
            # Make API call to Azure OpenAI
            response = self.client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Document content:\n\n{trimmed_text}"}
                ],
                temperature=0.7,  # Higher temperature for more creativity in questions
                response_format={"type": "json_object"}  # Request JSON
            )
            
            # Parse the JSON response
            result_text = response.choices[0].message.content
            try:
                parsed_response = json.loads(result_text)
                
                # Check if the response contains a questions or qa_pairs field
                if "questions" in parsed_response:
                    qa_pairs = parsed_response["questions"]
                elif "qa_pairs" in parsed_response:
                    qa_pairs = parsed_response["qa_pairs"]
                else:
                    # Use the entire response if it's an array
                    qa_pairs = parsed_response if isinstance(parsed_response, list) else parsed_response
                
                # Ensure we return a dictionary
                if isinstance(qa_pairs, list):
                    qa_pairs = {"qa_pairs": qa_pairs}
                    
            except json.JSONDecodeError:
                logger.warning("Failed to parse QA response as JSON")
                qa_pairs = {"qa_pairs": [], "warning": "Response was not valid JSON", "raw_text": result_text}
            
            # Add metadata
            result = {
                **qa_pairs,
                "model_used": model,
                "qa_prompt": qa_prompt,
                "processed_at": datetime.now().isoformat(),
                "token_usage": {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                }
            }
            
            logger.info(f"Successfully generated {len(qa_pairs.get('qa_pairs', []))} QA pairs using {model}")
            return result
            
        except Exception as e:
            logger.error(f"Error generating QA pairs: {str(e)}")
            return {
                "qa_pairs": [],
                "error": str(e),
                "processed_at": datetime.now().isoformat(),
                "model_used": model,
                "qa_prompt": qa_prompt,
                "status": "failed"
            }
    
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
            # Trim document if needed
            trimmed_text = self._trim_document_for_context(document_text)
            
            # Build system prompt for summarization
            system_prompt = f"""
            You are an expert document summarization system. Your task is to summarize the 
            document based on the following instructions:
            
            {summary_prompt}
            
            Provide your response as a JSON object with the following fields:
            - "summary": The main summary text
            - "key_points": An array of key points from the document
            - "document_type": The type or category of document
            - "metadata": Any relevant metadata about the document
            """
            
            # Make API call to Azure OpenAI
            response = self.client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Document content:\n\n{trimmed_text}"}
                ],
                temperature=0.3,  # Lower temperature for more factual summaries
                response_format={"type": "json_object"}  # Request JSON
            )
            
            # Parse the JSON response
            result_text = response.choices[0].message.content
            try:
                summary_data = json.loads(result_text)
            except json.JSONDecodeError:
                logger.warning(f"Failed to parse JSON response: {result_text}")
                summary_data = {"summary": result_text, "warning": "Response was not valid JSON"}
            
            # Add metadata
            result = {
                **summary_data,
                "model_used": model,
                "summary_prompt": summary_prompt,
                "summary_length": len(summary_data.get("summary", "")),
                "processed_at": datetime.now().isoformat(),
                "token_usage": {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                }
            }
            
            logger.info(f"Successfully summarized document using {model}")
            return result
            
        except Exception as e:
            logger.error(f"Error summarizing document: {str(e)}")
            return {
                "error": str(e),
                "processed_at": datetime.now().isoformat(),
                "model_used": model,
                "summary_prompt": summary_prompt,
                "status": "failed"
            }

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
            # Trim document if needed
            trimmed_text = self._trim_document_for_context(document_text)
            
            # Build system prompt for entity extraction
            system_prompt = f"""
            You are an expert entity extraction system. Your task is to identify and extract named entities
            from the document based on the following instructions:
            
            {entity_prompt}
            
            Format your response as a valid JSON object where:
            - Each key is an entity type (e.g., "people", "organizations", "locations")
            - Each value is an array of entity objects with these properties:
              - "text": The exact text of the entity
              - "start": Approximate character position where entity starts (if known)
              - "confidence": Your confidence score (0.0-1.0)
              - "metadata": Any additional attributes relevant to this entity type
            """
            
            # Make API call to Azure OpenAI
            response = self.client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Document content:\n\n{trimmed_text}"}
                ],
                temperature=0.3,
                response_format={"type": "json_object"}
            )
            
            # Parse the JSON response
            result_text = response.choices[0].message.content
            try:
                entities = json.loads(result_text)
            except json.JSONDecodeError:
                logger.warning(f"Failed to parse JSON response: {result_text}")
                entities = {"warning": "Response was not valid JSON", "raw_text": result_text}
            
            # Add metadata
            result = {
                **entities,
                "model_used": model,
                "entity_prompt": entity_prompt,
                "processed_at": datetime.now().isoformat(),
                "token_usage": {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                }
            }
            
            logger.info(f"Successfully extracted entities using {model}")
            return result
            
        except Exception as e:
            logger.error(f"Error extracting entities: {str(e)}")
            return {
                "error": str(e),
                "processed_at": datetime.now().isoformat(),
                "model_used": model,
                "entity_prompt": entity_prompt,
                "status": "failed"
            }
    
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
            # Trim document if needed
            trimmed_text = self._trim_document_for_context(document_text)
            
            # Build system prompt for classification
            system_prompt = f"""
            You are an expert document classification system. Your task is to classify the document
            based on the following classification criteria:
            
            {classification_prompt}
            
            Format your response as a valid JSON object with these fields:
            - "primary_class": The main category for this document
            - "sub_classes": Array of more specific classifications if applicable
            - "confidence": Your confidence score for the classification (0.0-1.0)
            - "reasoning": Brief explanation of why this classification was chosen
            """
            
            # Make API call to Azure OpenAI
            response = self.client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Document content:\n\n{trimmed_text}"}
                ],
                temperature=0.3,
                response_format={"type": "json_object"}
            )
            
            # Parse the JSON response
            result_text = response.choices[0].message.content
            try:
                classification = json.loads(result_text)
            except json.JSONDecodeError:
                logger.warning(f"Failed to parse JSON response: {result_text}")
                classification = {"primary_class": "unknown", "warning": "Response was not valid JSON"}
            
            # Add metadata
            result = {
                **classification,
                "model_used": model,
                "classification_prompt": classification_prompt,
                "processed_at": datetime.now().isoformat(),
                "token_usage": {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                }
            }
            
            logger.info(f"Successfully classified document using {model}")
            return result
            
        except Exception as e:
            logger.error(f"Error classifying document: {str(e)}")
            return {
                "error": str(e),
                "processed_at": datetime.now().isoformat(),
                "model_used": model,
                "classification_prompt": classification_prompt,
                "status": "failed"
            }
    
    def _build_system_prompt(self, extraction_prompt: str, custom_fields: Optional[Dict[str, str]] = None) -> str:
        """Build the system prompt for structured data extraction."""
        # Base system prompt
        prompt = f"""
        You are an expert data extraction assistant. Your task is to extract structured information
        from the document text provided by the user based on the following extraction criteria:
        
        {extraction_prompt}
        
        Extract all information that matches these criteria. Structure your response as a clean, 
        well-formatted JSON object without any preamble or explanation text.
        """
        
        # Add custom fields if provided
        if custom_fields and len(custom_fields) > 0:
            prompt += "\n\nExtract these specific fields with their descriptions:"
            for field, description in custom_fields.items():
                prompt += f"\n- {field}: {description}"
        
        prompt += """
        When extracting data:
        1. Only include fields you're confident about
        2. Use null for missing values
        3. Maintain proper data types (strings, numbers, booleans, arrays)
        4. Use nested objects when appropriate
        5. Include confidence scores when possible
        """
        
        return prompt
    
    def _trim_document_for_context(self, document_text: str, max_tokens: int = 16000) -> str:
        """
        Trim document text to fit within token limit.
        
        Args:
            document_text: Original document text
            max_tokens: Maximum tokens to include
            
        Returns:
            Trimmed document text
        """
        # Simple estimation: ~4 characters per token for English text
        char_limit = max_tokens * 4
        
        if len(document_text) <= char_limit:
            return document_text
        
        # If document is too large, take first 75% and last 25% of the limit
        first_part = int(char_limit * 0.75)
        last_part = char_limit - first_part
        
        trimmed_text = document_text[:first_part] + "\n\n[...content trimmed...]\n\n" + document_text[-last_part:]
        return trimmed_text
    
    async def process_batch_async(
        self, 
        documents: List[Dict[str, str]], 
        extraction_prompt: str,
        extraction_type: str = "structured_data",
        **kwargs
    ) -> List[Dict[str, Any]]:
        """
        Process a batch of documents asynchronously.
        
        Args:
            documents: List of documents with their text content
            extraction_prompt: Prompt describing what to extract
            extraction_type: Type of extraction to perform
            **kwargs: Additional parameters for specific extraction types
            
        Returns:
            List of processing results
        """
        tasks = []
        
        for doc in documents:
            document_id = doc.get("id", "unknown")
            text = doc.get("text", "")
            
            if extraction_type == "structured_data":
                tasks.append(self._extract_structured_data_async(doc, extraction_prompt, **kwargs))
            elif extraction_type == "qa_generation":
                tasks.append(self._generate_qa_pairs_async(doc, extraction_prompt, **kwargs))
            elif extraction_type == "summarization":
                tasks.append(self._summarize_document_async(doc, extraction_prompt, **kwargs))
            elif extraction_type == "entity_extraction":
                tasks.append(self._extract_entities_async(doc, extraction_prompt, **kwargs))
            elif extraction_type == "classification":
                tasks.append(self._classify_document_async(doc, extraction_prompt, **kwargs))
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results and handle exceptions
        processed_results = []
        for i, result in enumerate(results):
            doc_id = documents[i].get("id", f"doc_{i}")
            
            if isinstance(result, Exception):
                processed_results.append({
                    "document_id": doc_id,
                    "status": "error",
                    "error": str(result),
                    "processed_at": datetime.now().isoformat()
                })
            else:
                result["document_id"] = doc_id
                processed_results.append(result)
        
        return processed_results
    
    async def _extract_structured_data_async(self, document: Dict[str, str], prompt: str, **kwargs):
        """Async version of extract_structured_data for batch processing."""
        try:
            return await asyncio.to_thread(
                self.extract_structured_data,
                document.get("text", ""),
                prompt,
                **kwargs
            )
        except Exception as e:
            logger.error(f"Error in async structured data extraction: {str(e)}")
            return e
    
    async def _generate_qa_pairs_async(self, document: Dict[str, str], prompt: str, **kwargs):
        """Async version of generate_qa_pairs for batch processing."""
        try:
            return await asyncio.to_thread(
                self.generate_qa_pairs,
                document.get("text", ""),
                prompt,
                **kwargs
            )
        except Exception as e:
            logger.error(f"Error in async QA generation: {str(e)}")
            return e
    
    async def _summarize_document_async(self, document: Dict[str, str], prompt: str, **kwargs):
        """Async version of summarize_document for batch processing."""
        try:
            return await asyncio.to_thread(
                self.summarize_document,
                document.get("text", ""),
                prompt,
                **kwargs
            )
        except Exception as e:
            logger.error(f"Error in async document summarization: {str(e)}")
            return e
    
    async def _extract_entities_async(self, document: Dict[str, str], prompt: str, **kwargs):
        """Async version of extract_entities for batch processing."""
        try:
            return await asyncio.to_thread(
                self.extract_entities,
                document.get("text", ""),
                prompt,
                **kwargs
            )
        except Exception as e:
            logger.error(f"Error in async entity extraction: {str(e)}")
            return e
    
    async def _classify_document_async(self, document: Dict[str, str], prompt: str, **kwargs):
        """Async version of classify_document for batch processing."""
        try:
            return await asyncio.to_thread(
                self.classify_document,
                document.get("text", ""),
                prompt,
                **kwargs
            )
        except Exception as e:
            logger.error(f"Error in async document classification: {str(e)}")
            return e