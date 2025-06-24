from azure.ai.formrecognizer import DocumentAnalysisClient
from azure.core.credentials import AzureKeyCredential
from azure.identity import DefaultAzureCredential
import logging
from typing import Dict, List, Optional, Any
import asyncio

logger = logging.getLogger(__name__)

class AzureFormRecognizerService:
    """Service for Azure Form Recognizer document analysis."""
    
    def __init__(self, endpoint: str, credential: Optional[str] = None):
        """
        Initialize the Azure Form Recognizer service.
        
        Args:
            endpoint: Azure Form Recognizer endpoint URL
            credential: API key (optional, uses managed identity if not provided)
        """
        self.endpoint = endpoint
        
        if credential:
            self.credential = AzureKeyCredential(credential)
        else:
            # Use managed identity in production
            self.credential = DefaultAzureCredential()
        
        self.client = DocumentAnalysisClient(
            endpoint=self.endpoint,
            credential=self.credential
        )
    
    def extract_text_from_pdf(self, file_path: str) -> Dict[str, Any]:
        """
        Extract text and structure from PDF using Form Recognizer.
        
        Args:
            file_path: Path to PDF file
            
        Returns:
            Extracted text and metadata
        """
        try:
            with open(file_path, "rb") as file:
                # Use prebuilt-read model for general document analysis
                poller = self.client.begin_analyze_document(
                    "prebuilt-read", 
                    document=file
                )
                result = poller.result()
            
            # Extract content
            extracted_data = {
                "content": result.content,
                "pages": [],
                "tables": [],
                "paragraphs": [],
                "confidence": 0.0
            }
            
            # Process pages
            for page in result.pages:
                page_data = {
                    "page_number": page.page_number,
                    "text": "",
                    "lines": [],
                    "width": page.width,
                    "height": page.height,
                    "unit": page.unit
                }
                
                if page.lines:
                    for line in page.lines:
                        line_data = {
                            "content": line.content,
                            "bounding_box": [point for point in line.polygon] if line.polygon else [],
                            "confidence": getattr(line, 'confidence', 0.0)
                        }
                        page_data["lines"].append(line_data)
                        page_data["text"] += line.content + "\n"
                
                extracted_data["pages"].append(page_data)
            
            # Process tables
            if result.tables:
                for table in result.tables:
                    table_data = {
                        "row_count": table.row_count,
                        "column_count": table.column_count,
                        "cells": []
                    }
                    
                    for cell in table.cells:
                        cell_data = {
                            "content": cell.content,
                            "row_index": cell.row_index,
                            "column_index": cell.column_index,
                            "row_span": getattr(cell, 'row_span', 1),
                            "column_span": getattr(cell, 'column_span', 1),
                            "confidence": getattr(cell, 'confidence', 0.0)
                        }
                        table_data["cells"].append(cell_data)
                    
                    extracted_data["tables"].append(table_data)
            
            # Process paragraphs
            if result.paragraphs:
                for paragraph in result.paragraphs:
                    paragraph_data = {
                        "content": paragraph.content,
                        "bounding_regions": [],
                        "role": getattr(paragraph, 'role', None)
                    }
                    
                    if paragraph.bounding_regions:
                        for region in paragraph.bounding_regions:
                            region_data = {
                                "page_number": region.page_number,
                                "polygon": [point for point in region.polygon] if region.polygon else []
                            }
                            paragraph_data["bounding_regions"].append(region_data)
                    
                    extracted_data["paragraphs"].append(paragraph_data)
            
            # Calculate overall confidence
            total_confidence = 0
            confidence_count = 0
            
            for page in extracted_data["pages"]:
                for line in page.get("lines", []):
                    if "confidence" in line:
                        total_confidence += line["confidence"]
                        confidence_count += 1
            
            if confidence_count > 0:
                extracted_data["confidence"] = total_confidence / confidence_count
            
            logger.info(f"Successfully extracted text from PDF: {file_path}")
            return extracted_data
            
        except Exception as e:
            logger.error(f"Error extracting text from PDF {file_path}: {str(e)}")
            raise
    
    def analyze_document_structure(self, file_path: str) -> Dict[str, Any]:
        """
        Analyze document structure and layout.
        
        Args:
            file_path: Path to PDF file
            
        Returns:
            Document structure analysis
        """
        try:
            with open(file_path, "rb") as file:
                # Use prebuilt-layout model for structure analysis
                poller = self.client.begin_analyze_document(
                    "prebuilt-layout", 
                    document=file
                )
                result = poller.result()
            
            structure_data = {
                "document_type": "pdf",
                "page_count": len(result.pages),
                "has_tables": len(result.tables) > 0 if result.tables else False,
                "table_count": len(result.tables) if result.tables else 0,
                "paragraph_count": len(result.paragraphs) if result.paragraphs else 0,
                "styles": [],
                "sections": []
            }
            
            # Analyze styles
            if result.styles:
                for style in result.styles:
                    style_data = {
                        "style_name": style.name if hasattr(style, 'name') else "unknown",
                        "confidence": style.confidence if hasattr(style, 'confidence') else 0.0,
                        "appearance": {}
                    }
                    
                    # Safely check if appearance attribute exists before trying to access its properties
                    if hasattr(style, 'appearance'):
                        appearance = style.appearance
                        style_data["appearance"] = {
                            "font_family": appearance.font_family if hasattr(appearance, 'font_family') else None,
                            "font_size": appearance.font_size if hasattr(appearance, 'font_size') else None,
                            "font_weight": appearance.font_weight if hasattr(appearance, 'font_weight') else None,
                            "font_style": appearance.font_style if hasattr(appearance, 'font_style') else None,
                            "color": appearance.color if hasattr(appearance, 'color') else None
                        }
                    structure_data["styles"].append(style_data)
            
            logger.info(f"Successfully analyzed document structure: {file_path}")
            return structure_data
            
        except Exception as e:
            logger.error(f"Error analyzing document structure {file_path}: {str(e)}")
            raise
    
    def extract_key_value_pairs(self, file_path: str) -> Dict[str, Any]:
        """
        Extract key-value pairs from document.
        
        Args:
            file_path: Path to PDF file
            
        Returns:
            Extracted key-value pairs
        """
        try:
            with open(file_path, "rb") as file:
                # Use prebuilt-document model for key-value extraction
                poller = self.client.begin_analyze_document(
                    "prebuilt-document", 
                    document=file
                )
                result = poller.result()
            
            kv_data = {
                "key_value_pairs": [],
                "confidence": 0.0
            }
            
            if result.key_value_pairs:
                total_confidence = 0
                for kv_pair in result.key_value_pairs:
                    kv_item = {
                        "key": kv_pair.key.content if kv_pair.key else None,
                        "value": kv_pair.value.content if kv_pair.value else None,
                        "key_confidence": kv_pair.key.confidence if kv_pair.key and hasattr(kv_pair.key, 'confidence') else 0.0,
                        "value_confidence": kv_pair.value.confidence if kv_pair.value and hasattr(kv_pair.value, 'confidence') else 0.0
                    }
                    
                    # Calculate confidence
                    pair_confidence = (kv_item["key_confidence"] + kv_item["value_confidence"]) / 2
                    total_confidence += pair_confidence
                    
                    # Add page numbers
                    key_page = kv_pair.key.bounding_regions[0].page_number if kv_pair.key and kv_pair.key.bounding_regions else None
                    value_page = kv_pair.value.bounding_regions[0].page_number if kv_pair.value and kv_pair.value.bounding_regions else None
                    
                    kv_item["key_page"] = key_page
                    kv_item["value_page"] = value_page
                    
                    kv_data["key_value_pairs"].append(kv_item)
                
                # Calculate average confidence
                if len(result.key_value_pairs) > 0:
                    kv_data["confidence"] = total_confidence / len(result.key_value_pairs)
            
            logger.info(f"Successfully extracted key-value pairs from: {file_path}")
            return kv_data
            
        except Exception as e:
            logger.error(f"Error extracting key-value pairs from {file_path}: {str(e)}")
            raise
