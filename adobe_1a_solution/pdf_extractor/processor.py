"""
Advanced processing functions and batch operations.
"""

import os
import json
import logging
import concurrent.futures
from pathlib import Path
from typing import List, Dict, Optional, Callable, Tuple
from datetime import datetime

from .extractor import PDFOutlineExtractor
from .utils import load_cache_file, save_cache_file, save_output_advanced


def process_single_pdf(pdf_path: str, extractor: PDFOutlineExtractor, 
                      cache: Dict, include_metadata: bool = False,
                      progress_callback: callable = None) -> Dict:
    """
    Process a single PDF file with caching support.
    
    Args:
        pdf_path: Path to PDF file
        extractor: PDFOutlineExtractor instance
        cache: Cache dictionary
        include_metadata: Whether to include metadata
        progress_callback: Optional progress callback
        
    Returns:
        Dictionary containing extraction results
    """
    filename = os.path.basename(pdf_path)
    
    try:
        # Check cache first
        is_cached, cached_result = extractor._is_cached(pdf_path, cache)
        if is_cached and cached_result:
            logging.info(f"Using cached result for {filename}")
            return {
                "filename": filename,
                "status": "success",
                "cached": True,
                **cached_result
            }
        
        # Process the PDF
        if progress_callback:
            progress_callback(f"Processing {filename}...")
        
        result = extractor.extract_outline(pdf_path, include_metadata, progress_callback)
        
        # Update cache
        if extractor.enable_cache:
            file_hash = extractor._generate_file_hash(pdf_path)
            if file_hash:
                cache[filename] = {
                    "hash": file_hash,
                    "result": result,
                    "timestamp": datetime.now().isoformat()
                }
        
        return {
            "filename": filename,
            "status": "success",
            "cached": False,
            **result
        }
        
    except Exception as e:
        error_msg = str(e)
        logging.error(f"Error processing {filename}: {error_msg}")
        return {
            "filename": filename,
            "status": "error",
            "error": error_msg,
            "title": "",
            "outline": []
        }


def process_pdfs_advanced(pdf_paths: List[str], output_dir: str = "outputs",
                         cache_file: str = "cache.json", parallel: bool = True,
                         max_workers: int = 4, include_metadata: bool = False,
                         output_formats: List[str] = None, 
                         config: Dict = None,
                         progress_callback: callable = None) -> Dict:
    """
    Advanced batch processing of PDFs with parallel execution and comprehensive output.
    
    Args:
        pdf_paths: List of PDF file paths to process
        output_dir: Directory to save output files
        cache_file: Path to cache file
        parallel: Whether to use parallel processing
        max_workers: Maximum number of worker threads
        include_metadata: Whether to include PDF metadata
        output_formats: List of output formats ('json', 'txt', 'md')
        config: Configuration dictionary for extractor
        progress_callback: Optional progress callback
        
    Returns:
        Dictionary containing processing results and statistics
    """
    if output_formats is None:
        output_formats = ['json']
    
    # Initialize extractor with configuration
    extractor_config = config or {}
    extractor = PDFOutlineExtractor(**extractor_config)
    
    # Load cache
    cache = load_cache_file(cache_file) if extractor.enable_cache else {}
    
    # Create output directory
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    results = []
    processing_stats = {
        "total_files": len(pdf_paths),
        "successful": 0,
        "failed": 0,
        "cached": 0,
        "start_time": datetime.now().isoformat(),
        "processing_times": []
    }
    
    if progress_callback:
        progress_callback(f"Starting batch processing of {len(pdf_paths)} PDFs...")
    
    if parallel and len(pdf_paths) > 1:
        # Parallel processing
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all tasks
            future_to_path = {
                executor.submit(
                    process_single_pdf, 
                    pdf_path, 
                    extractor, 
                    cache, 
                    include_metadata,
                    progress_callback
                ): pdf_path for pdf_path in pdf_paths
            }
            
            # Collect results
            for future in concurrent.futures.as_completed(future_to_path):
                pdf_path = future_to_path[future]
                try:
                    result = future.result()
                    results.append(result)
                    
                    # Update stats
                    if result["status"] == "success":
                        processing_stats["successful"] += 1
                        if result.get("cached", False):
                            processing_stats["cached"] += 1
                    else:
                        processing_stats["failed"] += 1
                    
                    if progress_callback:
                        progress_callback(f"Completed {len(results)}/{len(pdf_paths)} files")
                        
                except Exception as e:
                    logging.error(f"Future failed for {pdf_path}: {str(e)}")
                    results.append({
                        "filename": os.path.basename(pdf_path),
                        "status": "error",
                        "error": str(e),
                        "title": "",
                        "outline": []
                    })
                    processing_stats["failed"] += 1
    else:
        # Sequential processing
        for i, pdf_path in enumerate(pdf_paths):
            if progress_callback:
                progress_callback(f"Processing {i+1}/{len(pdf_paths)}: {os.path.basename(pdf_path)}")
            
            result = process_single_pdf(pdf_path, extractor, cache, include_metadata, progress_callback)
            results.append(result)
            
            # Update stats
            if result["status"] == "success":
                processing_stats["successful"] += 1
                if result.get("cached", False):
                    processing_stats["cached"] += 1
            else:
                processing_stats["failed"] += 1
    
    # Save cache
    if extractor.enable_cache and cache:
        save_cache_file(cache, cache_file)
    
    # Prepare summary data
    processing_stats["end_time"] = datetime.now().isoformat()
    processing_stats["success_rate"] = (processing_stats["successful"] / processing_stats["total_files"] * 100) if processing_stats["total_files"] > 0 else 0
    
    # Get extractor statistics
    extractor_stats = extractor.get_processing_stats()
    processing_stats.update({
        "total_headings_extracted": extractor_stats.get("total_headings", 0),
        "avg_headings_per_file": extractor_stats.get("avg_headings_per_file", 0),
        "avg_processing_time": extractor_stats.get("avg_processing_time", 0)
    })
    
    # Create comprehensive output
    output_data = {
        "processing_info": {
            "timestamp": datetime.now().isoformat(),
            "total_files": len(pdf_paths),
            "configuration": extractor_config,
            "output_formats": output_formats,
            "parallel_processing": parallel,
            "cache_enabled": extractor.enable_cache
        },
        "statistics": processing_stats,
        "results": results
    }
    
    # Save outputs in requested formats
    if progress_callback:
        progress_callback("Saving output files...")
    
    save_output_advanced(output_data, output_path, output_formats)
    
    if progress_callback:
        progress_callback(f"Batch processing complete! Processed {processing_stats['successful']}/{processing_stats['total_files']} files successfully")
    
    logging.info(f"Batch processing complete: {processing_stats['successful']}/{processing_stats['total_files']} successful")
    
    return output_data


def create_summary_report(results: List[Dict], output_path: Path) -> Dict:
    """
    Create a summary report of processing results.
    
    Args:
        results: List of processing results
        output_path: Path to save the report
        
    Returns:
        Dictionary containing summary statistics
    """
    summary = {
        "total_files": len(results),
        "successful_extractions": sum(1 for r in results if r["status"] == "success"),
        "failed_extractions": sum(1 for r in results if r["status"] == "error"),
        "cached_results": sum(1 for r in results if r.get("cached", False)),
        "total_headings": sum(len(r.get("outline", [])) for r in results if r["status"] == "success"),
        "files_with_no_headings": sum(1 for r in results if r["status"] == "success" and len(r.get("outline", [])) == 0),
        "files_with_many_headings": sum(1 for r in results if r["status"] == "success" and len(r.get("outline", [])) > 10),
        "avg_headings_per_file": 0,
        "success_rate": 0
    }
    
    if summary["successful_extractions"] > 0:
        summary["avg_headings_per_file"] = summary["total_headings"] / summary["successful_extractions"]
    
    if summary["total_files"] > 0:
        summary["success_rate"] = summary["successful_extractions"] / summary["total_files"] * 100
    
    # Detailed file analysis
    summary["file_analysis"] = []
    for result in results:
        if result["status"] == "success":
            summary["file_analysis"].append({
                "filename": result["filename"],
                "title": result.get("title", ""),
                "heading_count": len(result.get("outline", [])),
                "has_metadata": "metadata" in result,
                "cached": result.get("cached", False)
            })
        else:
            summary["file_analysis"].append({
                "filename": result["filename"],
                "status": "error",
                "error": result.get("error", "Unknown error")
            })
    
    # Common error analysis
    errors = [r.get("error", "") for r in results if r["status"] == "error"]
    error_types = {}
    for error in errors:
        error_type = error.split(":")[0] if ":" in error else error
        error_types[error_type] = error_types.get(error_type, 0) + 1
    
    summary["common_errors"] = error_types
    
    # Save summary report
    try:
        summary_path = output_path / "processing_summary.json"
        with open(summary_path, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        logging.info(f"Summary report saved to {summary_path}")
    except Exception as e:
        logging.error(f"Error saving summary report: {str(e)}")
    
    return summary


def validate_batch_input(pdf_paths: List[str]) -> Tuple[List[str], List[str]]:
    """
    Validate batch input and separate valid/invalid files.
    
    Args:
        pdf_paths: List of PDF file paths
        
    Returns:
        Tuple of (valid_paths, invalid_paths_with_reasons)
    """
    valid_paths = []
    invalid_paths = []
    
    for pdf_path in pdf_paths:
        if not os.path.exists(pdf_path):
            invalid_paths.append(f"{pdf_path}: File does not exist")
        elif not pdf_path.lower().endswith('.pdf'):
            invalid_paths.append(f"{pdf_path}: Not a PDF file")
        elif os.path.getsize(pdf_path) == 0:
            invalid_paths.append(f"{pdf_path}: Empty file")
        else:
            valid_paths.append(pdf_path)
    
    return valid_paths, invalid_paths


def estimate_processing_time(pdf_paths: List[str], parallel: bool = True, 
                           max_workers: int = 4) -> Dict:
    """
    Estimate processing time based on file sizes and system capabilities.
    
    Args:
        pdf_paths: List of PDF file paths
        parallel: Whether parallel processing will be used
        max_workers: Number of worker threads
        
    Returns:
        Dictionary containing time estimates
    """
    total_size = sum(os.path.getsize(path) for path in pdf_paths if os.path.exists(path))
    file_count = len(pdf_paths)
    
    # Rough estimates based on empirical testing
    # These are conservative estimates
    base_time_per_mb = 2.0  # seconds per MB
    base_time_per_file = 1.0  # seconds per file (overhead)
    
    total_mb = total_size / (1024 * 1024)
    sequential_time = (total_mb * base_time_per_mb) + (file_count * base_time_per_file)
    
    if parallel and file_count > 1:
        # Parallel processing reduces time but has diminishing returns
        effective_workers = min(max_workers, file_count)
        parallel_efficiency = 0.7  # Account for overhead and thread coordination
        parallel_time = (sequential_time / effective_workers) * (1 + (1 - parallel_efficiency))
    else:
        parallel_time = sequential_time
    
    return {
        "total_files": file_count,
        "total_size_mb": round(total_mb, 2),
        "estimated_sequential_time": round(sequential_time, 1),
        "estimated_parallel_time": round(parallel_time, 1),
        "recommended_parallel": file_count > 2 and total_mb > 5,
        "time_savings": round(sequential_time - parallel_time, 1) if parallel else 0
    }
