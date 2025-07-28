"""
Utility functions for PDF extraction system.
"""

import logging
import os
import json
from typing import Dict, List
from pathlib import Path


def setup_logging(log_level: str = "INFO", log_file: str = "pdf_outline_extractor.log"):
    """Setup enhanced logging configuration."""
    log_levels = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL
    }
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
    )
    
    # Setup file handler
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setFormatter(formatter)
    
    # Setup console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    
    # Configure logger
    logger = logging.getLogger(__name__)
    logger.setLevel(log_levels.get(log_level.upper(), logging.INFO))
    logger.handlers.clear()  # Clear existing handlers
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger


def load_cache_file(cache_file: str) -> Dict:
    """Load cache from file."""
    try:
        if os.path.exists(cache_file):
            with open(cache_file, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        logging.warning(f"Could not load cache: {e}")
    return {}


def save_cache_file(cache: Dict, cache_file: str):
    """Save cache to file."""
    try:
        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump(cache, f, indent=2, ensure_ascii=False)
    except Exception as e:
        logging.warning(f"Could not save cache: {e}")


def save_output_advanced(output: Dict, output_path: Path, output_formats: List[str]):
    """
    Save output in requested formats, optimized for JSON schema compliance.
    
    Args:
        output: Extracted data
        output_path: Output directory path
        output_formats: List of output formats ('json', 'txt', 'md')
    """
    output_path.mkdir(parents=True, exist_ok=True)
    
    for format_type in output_formats:
        try:
            if format_type.lower() == "json":
                # Schema-compliant JSON output - save individual files
                for result in output.get('results', []):
                    if result['status'] == 'success':
                        # Create schema-compliant structure
                        schema_output = {
                            "title": result.get('title', ''),
                            "outline": result.get('outline', [])
                        }
                        
                        # Save individual file result
                        filename = result['filename'].replace('.pdf', '.json')
                        file_path = output_path / filename
                        with open(file_path, 'w', encoding='utf-8') as f:
                            json.dump(schema_output, f, indent=2, ensure_ascii=False)
                        logging.info(f"Saved schema-compliant JSON to {file_path}")
            
            elif format_type.lower() == "txt":
                # Secondary format - plain text summary
                filename = "extraction_results.txt"
                file_path = output_path / filename
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write("PDF Outline Extraction Results\n")
                    f.write("="*50 + "\n\n")
                    
                    for result in output.get('results', []):
                        if result['status'] == 'success':
                            f.write(f"File: {result['filename']}\n")
                            f.write(f"Title: {result.get('title', 'No title')}\n")
                            f.write("-" * 30 + "\n")
                            
                            for item in result.get('outline', []):
                                indent = "  " * (int(item['level'][1:]) - 1)
                                f.write(f"{indent}- {item['text']} (Page {item['page']})\n")
                            f.write("\n")
                logging.info(f"Saved TXT output to {file_path}")
            
            elif format_type.lower() == "md":
                # Secondary format - markdown summary
                filename = "extraction_results.md"
                file_path = output_path / filename
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write("# PDF Outline Extraction Results\n\n")
                    
                    for result in output.get('results', []):
                        if result['status'] == 'success':
                            f.write(f"## {result['filename']}\n\n")
                            if result.get('title'):
                                f.write(f"**Title:** {result['title']}\n\n")
                            
                            f.write("### Outline\n\n")
                            for item in result.get('outline', []):
                                level = int(item['level'][1:])
                                prefix = "#" * (level + 3)
                                f.write(f"{prefix} {item['text']}\n")
                                f.write(f"*Page {item['page']}*\n\n")
                            f.write("---\n\n")
                logging.info(f"Saved MD output to {file_path}")
            
            else:
                raise ValueError(f"Unsupported format: {format_type}")
                
        except Exception as e:
            logging.error(f"Error saving {format_type} output: {str(e)}")
            raise
