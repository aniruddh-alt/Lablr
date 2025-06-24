from typing import Dict, List, Any, Optional, Union
from datetime import datetime
from pathlib import Path
import json
import pandas as pd
import logging
import os

logger = logging.getLogger(__name__)

class DataProcessor:
    """Service for processing and formatting extracted data."""
    
    def __init__(self, output_dir: str = "outputs"):
        """
        Initialize the data processor.
        
        Args:
            output_dir: Directory to save output files
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
    
    def process_extraction_results(
        self,
        results: List[Dict[str, Any]],
        output_format: str,
        extraction_type: str,
        job_name: str
    ) -> Dict[str, Any]:
        """
        Process extraction results into the specified format.
        
        Args:
            results: List of extraction results
            output_format: Desired output format
            extraction_type: Type of extraction performed
            job_name: Name of the extraction job
            
        Returns:
            Processing results with file paths and metadata
        """
        try:
            if output_format.lower() == "csv":
                return self._to_csv(results, extraction_type, job_name)
            elif output_format.lower() == "json":
                return self._to_json(results, job_name)
            elif output_format.lower() == "jsonl":
                return self._to_jsonl(results, job_name)
            elif output_format.lower() == "qa_pairs":
                return self._to_qa_pairs(results, job_name)
            elif output_format.lower() == "markdown":
                return self._to_markdown(results, extraction_type, job_name)
            elif output_format.lower() == "xlsx":
                return self._to_xlsx(results, extraction_type, job_name)
            else:
                # Default to JSON if format not recognized
                logger.warning(f"Unrecognized output format '{output_format}', defaulting to JSON")
                return self._to_json(results, job_name)
                
        except Exception as e:
            logger.error(f"Error processing extraction results: {str(e)}")
            raise
    
    def _to_csv(self, results: List[Dict[str, Any]], extraction_type: str, job_name: str) -> Dict[str, Any]:
        """Convert results to CSV format."""
        try:
            # Prepare data for CSV
            csv_data = []
            
            for result in results:
                # Skip failed extractions
                if result.get("status") == "error" or "error" in result:
                    continue
                
                document_id = result.get("document_id", "unknown")
                
                # Handle different extraction types
                if extraction_type == "structured_data":
                    # Get the extracted data
                    extracted = result.get("extracted_data", {})
                    if isinstance(extracted, dict):
                        # Flatten nested dictionaries
                        flattened = self._flatten_dict(extracted)
                        flattened["document_id"] = document_id
                        csv_data.append(flattened)
                
                elif extraction_type == "entity_extraction":
                    # For entities, create one row per entity
                    for entity_type, entities in result.items():
                        if isinstance(entities, list) and entity_type != "entity_types":
                            for entity in entities:
                                if isinstance(entity, dict):
                                    entity_row = {
                                        "document_id": document_id,
                                        "entity_type": entity_type,
                                        "entity_text": entity.get("text", ""),
                                        "confidence": entity.get("confidence", 0.0)
                                    }
                                    csv_data.append(entity_row)
                
                elif extraction_type == "classification":
                    # For classification, one row per document
                    csv_data.append({
                        "document_id": document_id,
                        "primary_class": result.get("primary_class", ""),
                        "confidence": result.get("confidence", 0.0),
                        "sub_classes": ", ".join(result.get("sub_classes", [])),
                        "reasoning": result.get("reasoning", "")
                    })
                
                else:
                    # Generic approach for other extraction types
                    result_copy = result.copy()
                    if "token_usage" in result_copy:
                        del result_copy["token_usage"]
                    flattened = self._flatten_dict(result_copy)
                    csv_data.append(flattened)
            
            # Create DataFrame and save to CSV
            if csv_data:
                df = pd.DataFrame(csv_data)
                
                # Generate filename
                filename = f"{job_name}_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
                file_path = self.output_dir / filename
                
                # Save to CSV
                df.to_csv(file_path, index=False)
                
                return {
                    "format": "csv",
                    "file_path": str(file_path),
                    "filename": filename,
                    "row_count": len(df),
                    "column_count": len(df.columns)
                }
            else:
                # No valid data to convert
                return {
                    "format": "csv",
                    "error": "No valid data to convert to CSV",
                    "row_count": 0
                }
                
        except Exception as e:
            logger.error(f"Error converting to CSV: {str(e)}")
            raise
    
    def _to_json(self, results: List[Dict[str, Any]], job_name: str) -> Dict[str, Any]:
        """Convert results to JSON format."""
        try:
            filename = f"{job_name}_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            file_path = self.output_dir / filename
            
            output_data = {
                "job_name": job_name,
                "generated_at": datetime.now().isoformat(),
                "total_documents": len(results),
                "successful_extractions": len([r for r in results if r.get("status") != "error" and "error" not in r]),
                "failed_extractions": len([r for r in results if r.get("status") == "error" or "error" in r]),
                "results": results
            }
            
            with open(file_path, 'w') as f:
                json.dump(output_data, f, indent=2)
            
            return {
                "format": "json",
                "file_path": str(file_path),
                "filename": filename,
                "document_count": len(results)
            }
            
        except Exception as e:
            logger.error(f"Error converting to JSON: {str(e)}")
            raise
    
    def _to_jsonl(self, results: List[Dict[str, Any]], job_name: str) -> Dict[str, Any]:
        """Convert results to JSONL format."""
        try:
            filename = f"{job_name}_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jsonl"
            file_path = self.output_dir / filename
            
            line_count = 0
            with open(file_path, 'w') as f:
                for result in results:
                    json.dump(result, f)
                    f.write('\n')
                    line_count += 1
            
            return {
                "format": "jsonl",
                "file_path": str(file_path),
                "filename": filename,
                "line_count": line_count
            }
            
        except Exception as e:
            logger.error(f"Error converting to JSONL: {str(e)}")
            raise
    
    def _to_qa_pairs(self, results: List[Dict[str, Any]], job_name: str) -> Dict[str, Any]:
        """Convert results to Q&A pairs format."""
        try:
            filename = f"{job_name}_qa_pairs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
            file_path = self.output_dir / filename
            
            json_filename = f"{job_name}_qa_pairs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            json_file_path = self.output_dir / json_filename
            
            qa_count = 0
            all_qa_pairs = []
            
            with open(file_path, 'w') as f:
                f.write(f"# {job_name} - Generated Q&A Pairs\n\n")
                f.write(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                
                for i, result in enumerate(results):
                    document_id = result.get("document_id", f"document_{i}")
                    
                    # Skip if there was an error or no QA pairs
                    if result.get("status") == "error" or "error" in result:
                        continue
                    
                    qa_pairs = result.get("qa_pairs", [])
                    if not qa_pairs:
                        continue
                    
                    # Write document header
                    f.write(f"## Document: {document_id}\n\n")
                    
                    # Write QA pairs
                    for j, qa in enumerate(qa_pairs):
                        if isinstance(qa, dict) and "question" in qa and "answer" in qa:
                            qa_count += 1
                            f.write(f"### Q{j+1}: {qa['question']}\n\n")
                            f.write(f"{qa['answer']}\n\n")
                            
                            # Add to all pairs with document reference
                            qa_with_source = {
                                "question": qa["question"],
                                "answer": qa["answer"],
                                "document_id": document_id,
                                "qa_id": f"{document_id}_q{j+1}"
                            }
                            all_qa_pairs.append(qa_with_source)
            
            # Save JSON format as well
            with open(json_file_path, 'w') as f:
                json.dump({
                    "job_name": job_name,
                    "generated_at": datetime.now().isoformat(),
                    "total_qa_pairs": qa_count,
                    "qa_pairs": all_qa_pairs
                }, f, indent=2)
            
            return {
                "format": "qa_pairs",
                "file_path": str(file_path),
                "json_file_path": str(json_file_path),
                "filename": filename,
                "json_filename": json_filename,
                "qa_count": qa_count
            }
            
        except Exception as e:
            logger.error(f"Error converting to QA pairs: {str(e)}")
            raise
    
    def _to_markdown(self, results: List[Dict[str, Any]], extraction_type: str, job_name: str) -> Dict[str, Any]:
        """Convert results to Markdown format."""
        try:
            filename = f"{job_name}_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
            file_path = self.output_dir / filename
            
            with open(file_path, 'w') as f:
                f.write(f"# {job_name} - Extraction Results\n\n")
                f.write(f"**Generated:** {datetime.now().isoformat()}\n")
                f.write(f"**Extraction Type:** {extraction_type}\n")
                f.write(f"**Document Count:** {len(results)}\n\n")
                
                for i, result in enumerate(results):
                    document_id = result.get("document_id", f"document_{i}")
                    
                    # Skip if error
                    if result.get("status") == "error" or "error" in result:
                        f.write(f"## Document: {document_id} (Error)\n\n")
                        f.write(f"Error: {result.get('error', 'Unknown error')}\n\n")
                        continue
                    
                    f.write(f"## Document: {document_id}\n\n")
                    
                    # Format based on extraction type
                    if extraction_type == "structured_data":
                        extracted = result.get("extracted_data", {})
                        f.write("### Extracted Data\n\n")
                        f.write("```json\n")
                        f.write(json.dumps(extracted, indent=2))
                        f.write("\n```\n\n")
                    
                    elif extraction_type == "qa_generation":
                        qa_pairs = result.get("qa_pairs", [])
                        f.write("### Generated Q&A Pairs\n\n")
                        for j, qa in enumerate(qa_pairs):
                            if isinstance(qa, dict) and "question" in qa and "answer" in qa:
                                f.write(f"**Q{j+1}:** {qa['question']}\n\n")
                                f.write(f"**A:** {qa['answer']}\n\n")
                    
                    elif extraction_type == "summarization":
                        f.write("### Summary\n\n")
                        f.write(result.get("summary", "No summary available"))
                        f.write("\n\n")
                        
                        if "key_points" in result and isinstance(result["key_points"], list):
                            f.write("### Key Points\n\n")
                            for point in result["key_points"]:
                                f.write(f"- {point}\n")
                            f.write("\n")
                    
                    elif extraction_type == "classification":
                        f.write("### Classification\n\n")
                        f.write(f"**Primary Class:** {result.get('primary_class', 'Unknown')}\n")
                        f.write(f"**Confidence:** {result.get('confidence', 0.0)}\n")
                        
                        if "reasoning" in result:
                            f.write(f"\n**Reasoning:** {result['reasoning']}\n")
                        
                        if "sub_classes" in result and isinstance(result["sub_classes"], list):
                            f.write("\n**Sub-classes:**\n")
                            for sub in result["sub_classes"]:
                                f.write(f"- {sub}\n")
                    
                    else:
                        # Generic approach
                        f.write("### Results\n\n")
                        f.write("```json\n")
                        f.write(json.dumps(result, indent=2, default=str))
                        f.write("\n```\n\n")
            
            return {
                "format": "markdown",
                "file_path": str(file_path),
                "filename": filename,
                "document_count": len(results)
            }
            
        except Exception as e:
            logger.error(f"Error converting to Markdown: {str(e)}")
            raise
    
    def _to_xlsx(self, results: List[Dict[str, Any]], extraction_type: str, job_name: str) -> Dict[str, Any]:
        """Convert results to Excel format."""
        try:
            filename = f"{job_name}_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            file_path = self.output_dir / filename
            
            # Create Excel writer
            with pd.ExcelWriter(file_path) as writer:
                # Main results sheet
                main_data = []
                for result in results:
                    # Skip failed extractions for main sheet
                    if result.get("status") == "error" or "error" in result:
                        continue
                    
                    # Create a row for each result
                    row = {
                        "document_id": result.get("document_id", "unknown"),
                        "status": result.get("status", "unknown"),
                        "processed_at": result.get("processed_at", ""),
                        "model_used": result.get("model_used", "")
                    }
                    main_data.append(row)
                
                if main_data:
                    df_main = pd.DataFrame(main_data)
                    df_main.to_excel(writer, sheet_name="Summary", index=False)
                
                # Extraction type specific sheets
                if extraction_type == "structured_data":
                    # Create a sheet for structured data
                    structured_data = []
                    for result in results:
                        if result.get("status") != "error" and "error" not in result:
                            doc_id = result.get("document_id", "unknown")
                            extracted = result.get("extracted_data", {})
                            if isinstance(extracted, dict):
                                flat_data = self._flatten_dict(extracted)
                                flat_data["document_id"] = doc_id
                                structured_data.append(flat_data)
                    
                    if structured_data:
                        df_structured = pd.DataFrame(structured_data)
                        df_structured.to_excel(writer, sheet_name="Structured_Data", index=False)
                
                elif extraction_type == "qa_generation":
                    # Create a sheet for QA pairs
                    qa_data = []
                    for result in results:
                        if result.get("status") != "error" and "error" not in result:
                            doc_id = result.get("document_id", "unknown")
                            qa_pairs = result.get("qa_pairs", [])
                            
                            for qa in qa_pairs:
                                qa_data.append({
                                    "document_id": doc_id,
                                    "question": qa.get("question", ""),
                                    "answer": qa.get("answer", ""),
                                    "confidence": qa.get("confidence", "")
                                })
                    
                    if qa_data:
                        df_qa = pd.DataFrame(qa_data)
                        df_qa.to_excel(writer, sheet_name="QA_Pairs", index=False)
                
                elif extraction_type == "entity_extraction":
                    # Create sheets for each entity type
                    entity_types = set()
                    for result in results:
                        if result.get("status") != "error" and "error" not in result:
                            # Find all entity types across all documents
                            for key in result.keys():
                                if isinstance(result[key], list) and key not in ["document_id", "status", "token_usage"]:
                                    entity_types.add(key)
                    
                    # For each entity type, create a sheet
                    for entity_type in entity_types:
                        entities = []
                        for result in results:
                            doc_id = result.get("document_id", "unknown")
                            if entity_type in result and isinstance(result[entity_type], list):
                                for entity in result[entity_type]:
                                    if isinstance(entity, dict):
                                        entity_data = entity.copy()
                                        entity_data["document_id"] = doc_id
                                        entities.append(entity_data)
                        
                        if entities:
                            df_entities = pd.DataFrame(entities)
                            sheet_name = entity_type[:31]  # Excel sheet names limited to 31 chars
                            df_entities.to_excel(writer, sheet_name=sheet_name, index=False)
            
            return {
                "format": "xlsx",
                "file_path": str(file_path),
                "filename": filename,
                "document_count": len(results)
            }
            
        except Exception as e:
            logger.error(f"Error converting to Excel: {str(e)}")
            raise
    
    def _flatten_dict(self, d: Dict[str, Any], parent_key: str = '', sep: str = '_') -> Dict[str, Any]:
        """Flatten nested dictionary for CSV/Excel output."""
        items = []
        for k, v in d.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            if isinstance(v, dict):
                items.extend(self._flatten_dict(v, new_key, sep=sep).items())
            elif isinstance(v, list):
                # Handle lists by joining with semicolons
                if all(isinstance(item, (str, int, float)) for item in v):
                    items.append((new_key, "; ".join(str(i) for i in v)))
                elif len(v) > 0 and all(isinstance(item, dict) for item in v):
                    # For lists of dicts, add the first few as columns
                    for i, item in enumerate(v[:3]):  # Limit to first 3 items
                        list_key = f"{new_key}_{i+1}"
                        items.extend(self._flatten_dict(item, list_key, sep=sep).items())
                else:
                    # Mixed or complex lists
                    items.append((new_key, str(v)))
            else:
                items.append((new_key, v))
        return dict(items)
    
    def get_output_file_info(self, file_path: str) -> Dict[str, Any]:
        """Get information about an output file."""
        try:
            path = Path(file_path)
            if not path.exists():
                return {"error": f"File not found: {file_path}"}
            
            file_info = {
                "file_path": str(path),
                "filename": path.name,
                "size_bytes": path.stat().st_size,
                "created": datetime.fromtimestamp(path.stat().st_ctime).isoformat(),
                "modified": datetime.fromtimestamp(path.stat().st_mtime).isoformat(),
                "format": path.suffix.lstrip('.')
            }
            
            # Add format-specific info
            if path.suffix.lower() == '.csv':
                with open(path, 'r') as f:
                    headers = f.readline().strip().split(',')
                    row_count = sum(1 for _ in f) + 1  # +1 for header
                
                file_info["headers"] = headers
                file_info["row_count"] = row_count
            
            elif path.suffix.lower() == '.json':
                with open(path, 'r') as f:
                    json_data = json.load(f)
                
                file_info["structure"] = "object" if isinstance(json_data, dict) else "array"
                if isinstance(json_data, dict):
                    file_info["keys"] = list(json_data.keys())
                elif isinstance(json_data, list):
                    file_info["count"] = len(json_data)
                    if json_data and isinstance(json_data[0], dict):
                        file_info["sample_keys"] = list(json_data[0].keys())
            
            return file_info
            
        except Exception as e:
            logger.error(f"Error getting file info: {str(e)}")
            return {"error": str(e)}
    
    def cleanup_old_files(self, days_old: int = 7):
        """Clean up output files older than specified days."""
        try:
            now = datetime.now()
            cutoff = now.timestamp() - (days_old * 24 * 60 * 60)
            
            count = 0
            for file_path in self.output_dir.glob("*"):
                if file_path.is_file():
                    mtime = file_path.stat().st_mtime
                    if mtime < cutoff:
                        file_path.unlink()
                        count += 1
            
            logger.info(f"Cleanup completed: removed {count} files older than {days_old} days")
            return {"removed_files": count, "days_threshold": days_old}
                    
        except Exception as e:
            logger.error(f"Error during file cleanup: {str(e)}")
            return {"error": str(e)}