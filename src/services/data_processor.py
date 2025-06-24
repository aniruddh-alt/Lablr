import pandas as pd
import json
import csv
import logging
from typing import Dict, List, Any, Optional, Union
import io
from datetime import datetime
import os
from pathlib import Path

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
                raise ValueError(f"Unsupported output format: {output_format}")
                
        except Exception as e:
            logger.error(f"Error processing extraction results: {str(e)}")
            raise
    
    def _to_csv(self, results: List[Dict[str, Any]], extraction_type: str, job_name: str) -> Dict[str, Any]:
        """Convert results to CSV format."""
        try:
            # Prepare data for CSV
            csv_data = []
            
            for result in results:
                if result.get("status") == "success" and "result" in result:
                    row = {
                        "document_id": result["document_id"],
                        "status": result["status"]
                    }
                    
                    # Extract the actual data based on extraction type
                    if extraction_type == "structured_data":
                        extracted_data = result["result"].get("extracted_data", {})
                        row.update(self._flatten_dict(extracted_data))
                    elif extraction_type == "classification":
                        classification_data = result["result"]
                        row.update({
                            "classification": classification_data.get("classification"),
                            "confidence": classification_data.get("confidence"),
                            "reasoning": classification_data.get("reasoning")
                        })
                    elif extraction_type == "entity_extraction":
                        entities = result["result"]
                        # Create columns for each entity type
                        for entity_type, entity_list in entities.items():
                            entity_texts = [entity.get("text", "") for entity in entity_list if isinstance(entity, dict)]
                            row[f"{entity_type}_entities"] = "; ".join(entity_texts)
                    elif extraction_type == "summarization":
                        summary_data = result["result"]
                        row.update(self._flatten_dict(summary_data))
                    elif extraction_type == "qa_generation":
                        qa_pairs = result["result"]
                        if isinstance(qa_pairs, list) and qa_pairs:
                            # For CSV, we'll create separate rows for each Q&A pair
                            for i, qa in enumerate(qa_pairs):
                                qa_row = row.copy()
                                qa_row.update({
                                    "question_number": i + 1,
                                    "question": qa.get("question", ""),
                                    "answer": qa.get("answer", "")
                                })
                                csv_data.append(qa_row)
                            continue
                    
                    csv_data.append(row)
                else:
                    # Handle failed extractions
                    csv_data.append({
                        "document_id": result["document_id"],
                        "status": result.get("status", "error"),
                        "error": result.get("error", "Unknown error")
                    })
            
            # Create DataFrame and save to CSV
            if csv_data:
                df = pd.DataFrame(csv_data)
                filename = f"{job_name}_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
                file_path = self.output_dir / filename
                df.to_csv(file_path, index=False)
                
                return {
                    "format": "csv",
                    "file_path": str(file_path),
                    "filename": filename,
                    "row_count": len(df),
                    "column_count": len(df.columns),
                    "columns": list(df.columns)
                }
            else:
                raise ValueError("No data to convert to CSV")
                
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
                "generated_at": datetime.utcnow().isoformat(),
                "total_documents": len(results),
                "successful_extractions": len([r for r in results if r.get("status") == "success"]),
                "failed_extractions": len([r for r in results if r.get("status") != "success"]),
                "results": results
            }
            
            with open(file_path, 'w') as f:
                json.dump(output_data, f, indent=2, default=str)
            
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
            
            with open(file_path, 'w') as f:
                for result in results:
                    json.dump(result, f, default=str)
                    f.write('\n')
            
            return {
                "format": "jsonl",
                "file_path": str(file_path),
                "filename": filename,
                "line_count": len(results)
            }
            
        except Exception as e:
            logger.error(f"Error converting to JSONL: {str(e)}")
            raise
    
    def _to_qa_pairs(self, results: List[Dict[str, Any]], job_name: str) -> Dict[str, Any]:
        """Convert results to Q&A pairs format."""
        try:
            qa_pairs = []
            
            for result in results:
                if result.get("status") == "success" and "result" in result:
                    qa_data = result["result"]
                    if isinstance(qa_data, list):
                        # Direct Q&A pairs
                        for qa in qa_data:
                            if isinstance(qa, dict) and "question" in qa and "answer" in qa:
                                qa_pairs.append({
                                    "document_id": result["document_id"],
                                    "question": qa["question"],
                                    "answer": qa["answer"]
                                })
                    elif isinstance(qa_data, dict) and "qa_pairs" in qa_data:
                        # Q&A pairs in nested structure
                        for qa in qa_data["qa_pairs"]:
                            if isinstance(qa, dict) and "question" in qa and "answer" in qa:
                                qa_pairs.append({
                                    "document_id": result["document_id"],
                                    "question": qa["question"],
                                    "answer": qa["answer"]
                                })
            
            # Save as JSON
            filename = f"{job_name}_qa_pairs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            file_path = self.output_dir / filename
            
            output_data = {
                "job_name": job_name,
                "generated_at": datetime.utcnow().isoformat(),
                "total_qa_pairs": len(qa_pairs),
                "qa_pairs": qa_pairs
            }
            
            with open(file_path, 'w') as f:
                json.dump(output_data, f, indent=2, default=str)
            
            return {
                "format": "qa_pairs",
                "file_path": str(file_path),
                "filename": filename,
                "qa_pair_count": len(qa_pairs)
            }
            
        except Exception as e:
            logger.error(f"Error converting to Q&A pairs: {str(e)}")
            raise
    
    def _to_markdown(self, results: List[Dict[str, Any]], extraction_type: str, job_name: str) -> Dict[str, Any]:
        """Convert results to Markdown format."""
        try:
            filename = f"{job_name}_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
            file_path = self.output_dir / filename
            
            with open(file_path, 'w') as f:
                f.write(f"# {job_name} - Extraction Results\n\n")
                f.write(f"**Generated:** {datetime.utcnow().isoformat()}\n")
                f.write(f"**Extraction Type:** {extraction_type}\n")
                f.write(f"**Total Documents:** {len(results)}\n\n")
                
                for i, result in enumerate(results, 1):
                    f.write(f"## Document {i}: {result['document_id']}\n\n")
                    
                    if result.get("status") == "success" and "result" in result:
                        if extraction_type == "qa_generation":
                            qa_pairs = result["result"]
                            if isinstance(qa_pairs, list):
                                for j, qa in enumerate(qa_pairs, 1):
                                    f.write(f"### Q&A Pair {j}\n")
                                    f.write(f"**Question:** {qa.get('question', 'N/A')}\n\n")
                                    f.write(f"**Answer:** {qa.get('answer', 'N/A')}\n\n")
                        elif extraction_type == "summarization":
                            summary = result["result"]
                            for key, value in summary.items():
                                f.write(f"**{key.replace('_', ' ').title()}:** {value}\n\n")
                        else:
                            # Generic format for other types
                            data = result["result"]
                            if isinstance(data, dict):
                                for key, value in data.items():
                                    f.write(f"**{key.replace('_', ' ').title()}:** {value}\n\n")
                    else:
                        f.write(f"**Status:** {result.get('status', 'error')}\n")
                        f.write(f"**Error:** {result.get('error', 'Unknown error')}\n\n")
                    
                    f.write("---\n\n")
            
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
            
            with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
                # Summary sheet
                summary_data = {
                    "Metric": ["Total Documents", "Successful Extractions", "Failed Extractions", "Generated At"],
                    "Value": [
                        len(results),
                        len([r for r in results if r.get("status") == "success"]),
                        len([r for r in results if r.get("status") != "success"]),
                        datetime.utcnow().isoformat()
                    ]
                }
                summary_df = pd.DataFrame(summary_data)
                summary_df.to_excel(writer, sheet_name='Summary', index=False)
                
                # Results sheet (similar to CSV logic)
                csv_data = []
                for result in results:
                    if result.get("status") == "success" and "result" in result:
                        row = {
                            "document_id": result["document_id"],
                            "status": result["status"]
                        }
                        
                        if extraction_type == "structured_data":
                            extracted_data = result["result"].get("extracted_data", {})
                            row.update(self._flatten_dict(extracted_data))
                        elif extraction_type == "classification":
                            classification_data = result["result"]
                            row.update({
                                "classification": classification_data.get("classification"),
                                "confidence": classification_data.get("confidence"),
                                "reasoning": classification_data.get("reasoning")
                            })
                        
                        csv_data.append(row)
                    else:
                        csv_data.append({
                            "document_id": result["document_id"],
                            "status": result.get("status", "error"),
                            "error": result.get("error", "Unknown error")
                        })
                
                if csv_data:
                    results_df = pd.DataFrame(csv_data)
                    results_df.to_excel(writer, sheet_name='Results', index=False)
            
            return {
                "format": "xlsx",
                "file_path": str(file_path),
                "filename": filename,
                "sheet_count": 2
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
                # Convert lists to comma-separated strings
                items.append((new_key, ', '.join(map(str, v))))
            else:
                items.append((new_key, v))
        return dict(items)
    
    def get_output_file_info(self, file_path: str) -> Dict[str, Any]:
        """Get information about an output file."""
        try:
            path = Path(file_path)
            if not path.exists():
                return {"error": "File not found"}
            
            stat = path.stat()
            return {
                "filename": path.name,
                "size_bytes": stat.st_size,
                "size_mb": round(stat.st_size / (1024 * 1024), 2),
                "created_at": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                "modified_at": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                "extension": path.suffix
            }
            
        except Exception as e:
            logger.error(f"Error getting file info: {str(e)}")
            return {"error": str(e)}
    
    def cleanup_old_files(self, days_old: int = 7):
        """Clean up output files older than specified days."""
        try:
            cutoff_time = datetime.now().timestamp() - (days_old * 24 * 3600)
            
            for file_path in self.output_dir.iterdir():
                if file_path.is_file() and file_path.stat().st_mtime < cutoff_time:
                    file_path.unlink()
                    logger.info(f"Deleted old output file: {file_path.name}")
                    
        except Exception as e:
            logger.error(f"Error cleaning up old files: {str(e)}") 